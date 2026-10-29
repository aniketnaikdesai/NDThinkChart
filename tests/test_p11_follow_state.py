"""P11-T1: follow-state definition + repro probes (D51.1; S-P11-1) — pytest half.

The behavioural offscreen probes live in ``chart_assets/lwc/chart.test.js``
(``node --test``: a seeded series driven through the real ``lwApplyOps`` and
queried through the real ``lwFollowProbe`` / ``lwVisibleRange`` /
``lwIsFollowing`` surface, including the real ``bindKeyboard`` pan path for
AR-P11-1). This module is the static half: it pins the page-side probe
surface the JS suite drives (red pre-fix — the current tree had no follow
surface at all) and characterises the pre-fix unconditional refit inside
``applyOps`` (the yank W2 gates per S-P11-2).

Both tests run without a renderer (plain source assertions), so they hold on
an engine-less box exactly like the ``test_lwc_page_wiring`` probe-surface
suite they sit beside.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHART_JS = REPO / "chart_assets" / "lwc" / "chart.js"


def _src() -> str:
    return CHART_JS.read_text(encoding="utf-8")


def _apply_ops_body(src: str) -> str:
    start = src.index("function applyOps(env)")
    end = src.index("function applyRows(", start)
    return src[start:end]


def test_p11_t1_t11_follow_state_probe_surface():
    """P11-T1-T11 (AC-D51.1, static half): the follow-state surface exists.

    Pre-fix this fails — ``chart.js`` exposed no ``isFollowing`` surface, no
    newest-slot derivation and no offscreen-queryable probe. Post-fix the
    page derives follow state on query (newest bar's logical slot inside the
    live ``getVisibleLogicalRange()``), never stored, so every gesture —
    mouse, keyboard, wheel — is reflected by construction (AR-P11-1).
    """
    src = _src()
    # The derived predicate: following iff the newest bar's logical slot is
    # inside the visible logical range; empty / unlaid-out charts never follow.
    assert "function isFollowingSlot(newestSlot, range)" in src
    assert "slot >= from && slot <= to" in src
    assert "function isFollowing()" in src
    assert "snapshot.candles.length - 1" in src
    assert "getVisibleLogicalRange()" in src
    # Offscreen-queryable probes (what the node suite drives).
    assert "window.lwIsFollowing = isFollowing" in src
    assert "window.lwFollowProbe = function" in src
    # Pure core export so `node --test` covers the predicate without a page.
    assert "isFollowingSlot: isFollowingSlot" in src


def test_p11_t1_t12_visible_range_probe_and_unconditional_refit():
    """P11-T1-T12 (AC-D51.2 post-W2, static half): range probe + follow gating.

    The visible-range probe reports the newest slot alongside the library's
    own ``getVisibleLogicalRange()`` so later waves can assert viewport
    identity without re-deriving geometry. And ``applyOps`` now consults
    follow gating (W2/S-P11-2 landed): it captures ``isFollowing()`` BEFORE
    the rows land — appending a new period moves the newest slot, so a
    post-update check would read every live edge as scrolled back — and live
    upserts follow only while following, leaving a scrolled-back viewport
    bit-identical. The unconditional ``fitToWidth()`` yank baseline is gone;
    refit survives only on gated paths (replace fallback / new-symbol load).
    """
    src = _src()
    assert "window.lwVisibleRange = function" in src
    assert "newestSlot" in src
    body = _apply_ops_body(src)
    assert "isFollowing()" in body, (
        "applyOps must consult follow gating (W2/S-P11-2 landed)"
    )
    assert "followingBefore" in body, (
        "follow state must be captured BEFORE the upserts land"
    )
    assert "fitToWidth" in body, (
        "gated refit paths must remain (replace fallback / new-symbol load)"
    )
    assert "followLive" in body, (
        "live upserts must route through the follow-gated realtime scroll"
    )
