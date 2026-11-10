"""P21-T1: follow-offset live path — static/contract half (D60.1/D60.2/D60.5).

The behavioural viewport-slot matrices live in
``chart_assets/lwc/follow_offset.test.js`` (``node --test``: seeded series
driven through the real ``lwApplyOps`` and queried through the real
``lwFollowProbe`` / ``lwVisibleRange`` / ``lwIsFollowing`` /
``lwRememberedGap`` probes, including the real ``bindKeyboard`` pan path).
This module is the static half: it pins the page-side surfaces the node
suite drives (red pre-fix — the follow path edge-pinned via
``scrollToRealTime`` and no per-instance gap existed at all) and the
page/Python gap-boundary contract (no gap crosses the bridge; the default
mirrors ``FRESH_FRAME_RIGHT_PADDING``).

All tests run without a renderer (plain source assertions), so they hold on
an engine-less box exactly like the ``test_p11_follow_state`` probe-surface
suite they sit beside.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHART_JS = REPO / "chart_assets" / "lwc" / "chart.js"
LWC_VIEW = REPO / "ui" / "lwc_view.py"


def _src() -> str:
    return CHART_JS.read_text(encoding="utf-8")


def _apply_ops_body(src: str) -> str:
    start = src.index("function applyOps(env)")
    end = src.index("function applyRows(", start)
    return src[start:end]


def _fn_body(src: str, name: str) -> str:
    start = src.index(f"function {name}(")
    # Every page function ends before the next two-space-indented comment or
    # function at the same level; slice to the next "\n  function " / "\n  /*".
    tail = src[start:]
    nxt = len(tail)
    for marker in ("\n  function ", "\n  /*"):
        i = tail.find(marker, 1)
        if i != -1:
            nxt = min(nxt, i)
    return tail[:nxt]


def test_p21_t1_ac1_envelope_slot_delta_shift():
    """P21-T1-AC1 (AC-D60.1, static half): the live path shifts by delta.

    Pre-fix this fails — ``followLive`` edge-pinned through
    ``scrollToRealTime`` (with a ``{slot - span, slot}`` fallback) and
    ``applyOps`` captured no pre-envelope range base.
    """
    src = _src()
    live = _fn_body(src, "followLive")
    assert "scrollToRealTime" not in live, "edge-pin is gone from followLive"
    assert "shiftBaseSlot" in live, "delta reads the pre-envelope slot base"
    assert "+ delta" in live, "range shifts by the envelope delta"
    assert "if (!(delta > 0)) return true" in live, (
        "forming-bar ticks (zero new slots) move nothing"
    )
    body = _apply_ops_body(src)
    assert "shiftBaseRange = visibleLogicalRange()" in body, (
        "pre-envelope range captured BEFORE the ops land"
    )
    assert "shiftBaseSlot = slotBefore" in body
    assert "newestBarSlot() - slotBefore" in body, (
        "delta is newest-after minus newest-before across the envelope"
    )
    assert "shiftTarget" in body, "preserved range shifts on the replace path"
    assert "preservedRange.from + slotDelta" in body
    assert "followingBefore && slotDelta > 0" in body, (
        "replace-path shift fires only while following on slot growth"
    )


def test_p21_t1_ac2_explicit_action_preserve():
    """P21-T1-AC2 (AC-D60.2, static half): resume preserves the gap.

    Pre-fix this fails — ``goToRealtime`` shared the edge-pin scroll and
    ``fitAndFollow`` was a bare fit; no remembered gap existed.
    """
    src = _src()
    resume = _fn_body(src, "goToRealtime")
    assert "slot + rememberedGap - span" in resume, (
        "chevron/goToRealtime keeps span, lands newest at the gap offset"
    )
    assert "slot + rememberedGap" in resume
    fit = _fn_body(src, "fitAndFollow")
    assert "Number(landed.to) + rememberedGap" in fit, (
        "fitAndFollow frames all loaded bars then extends to by the gap"
    )
    assert src.count("rememberedGap =") == 2, (
        "the gap is written only at init (default) and on observed "
        "following ranges — no explicit action ever zeroes it"
    )
    assert "rememberedGap = FRESH_FRAME_RIGHT_PADDING" in src
    assert "if (following) rememberedGap" in src.replace(
        "if (following) rememberedGap = Number(range.to) - slot",
        "if (following) rememberedGap",
    )


def test_p21_t1_ac3_per_view_gap_never_crosses_bridge():
    """P21-T1-AC3 (AC-D60.5, static half): per-instance gap, off the bridge.

    Pre-fix this fails — no per-instance gap state existed anywhere.
    """
    src = _src()
    assert "var rememberedGap" in src, "gap state is page-side instance state"
    assert "window.lwRememberedGap = function" in src, "gap is probe-only"
    assert '"gap"' not in src and "'gap'" not in src, (
        "no gap field is constructed anywhere near a payload"
    )
    assert "JSON.stringify({ key: String(key) })" in src, (
        "the only page-to-Python payload stays the key event"
    )
    page_default = re.search(
        r"var FRESH_FRAME_RIGHT_PADDING = (\d+)", src)
    assert page_default is not None, "page default is a named constant"
    py_src = LWC_VIEW.read_text(encoding="utf-8")
    py_default = re.search(r"FRESH_FRAME_RIGHT_PADDING = (\d+)", py_src)
    assert py_default is not None
    assert page_default.group(1) == py_default.group(1), (
        "page default mirrors ui/lwc_view.py FRESH_FRAME_RIGHT_PADDING"
    )


def test_p21_t1_ac4_envelope_delta_ticks_and_republish():
    """P21-T1-AC4 (AC-D60.7 envelope half, static half): exactly-once delta.

    Pre-fix this fails — the live path had no delta accounting at all.
    """
    src = _src()
    body = _apply_ops_body(src)
    assert body.count("followLive();") == 1, (
        "one live-path shift call per envelope (never per-op)"
    )
    assert body.count("setVisibleLogicalRange") == 1, (
        "one replace-path range application per envelope (never twice)"
    )
    assert "slotDelta" in body, "envelope-level delta accounting"


# -- P21-T3-AC2: batch gate history-intact (AC-D60.6, static) ---------------

MARKER_SENTENCE = "This is an existing repository."


def test_p21_t3_ac2_history_intact():
    """P21-T3-AC2 (AC-D60.6, static): marker + stack + D41-D60 present.

    The Existing Repository marker sentence and Current Tech Stack stay put,
    every decision from D41 through D60 is present with its reversals
    (D41-D53 land as ``### D<N>`` sections; D54-D60 land as
    ``## Phase P<N> (D<N>)`` / ``#### Journey — D<N>`` headings — the
    P20-T3-AC2 convention), and no pre-P21 wording is touched: this batch
    edits code + tests only, so the frozen requirements input is
    byte-identical to HEAD.
    """
    req = REPO / "docs" / "requirements" / "requirements.md"
    assert req.is_file(), "docs/requirements/requirements.md missing"
    text = req.read_text(encoding="utf-8")
    assert MARKER_SENTENCE in text, "Existing Repository marker sentence gone"
    assert "Current Tech Stack" in text, "Current Tech Stack section gone"
    missing = [n for n in range(41, 61)
               if not re.search(rf"(?m)^#{{2,4}}\s+.*\bD{n}\b", text)]
    assert not missing, f"requirement sections missing: {missing}"
    assert re.search(r"(?i)reversal", text), "reversal record missing"
    proc = subprocess.run(
        ["git", "diff", "HEAD", "--",
         "docs/requirements/requirements.md"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert proc.returncode == 0, f"git diff failed: {proc.stderr.strip()}"
    assert proc.stdout.strip() == "", (
        "docs/requirements/requirements.md differs from HEAD — "
        "pre-P21 wording was touched"
    )
