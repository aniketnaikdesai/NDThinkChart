"""P13-T5 — D49.5 shared-hold lifecycle probe (S-P13-5, wave W5 half).

Offscreen probe; no production-code change. Drives the shared-hold
lifecycle — main-chart same-symbol reload, pop-out attach/close, plus a
zero-owner case — records the RT hold count (``TickerSession._rt_holders``)
against active owners (attached views, plus the alarm monitor when it holds
the session) at each step, and commits the verdict to
``docs/p13_hold_probe_record.md``:

- ``lasting effect confirmed`` — the hold count exceeds active owners and
  the excess survives continued session use;
- ``no lasting effect`` — the count tracks owners at every live step and
  the zero-owner case returns it to zero.

The probe always lands green (it is the deliverable); a missing verdict or
an unasserted zero-owner case fails.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

from config import settings

SYMBOL = "HOLDA"
OTHER = "HOLDB"
TF = "5 mins"
BASE_TS = 1_760_000_000
NOW_TS = (BASE_TS // 300) * 300

RECORD_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "p13_hold_probe_record.md"
)

VERDICT_CONFIRMED = "lasting effect confirmed"
VERDICT_CLEAN = "no lasting effect"


def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([6001, 6002, 6003, 6004, 6005])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    # D42's depth floor (S17) can issue many chunks from one load, so hand out
    # historical reqIds unbounded rather than exhausting a fixed list.
    hids = itertools.count(6101)
    win.md_manager.req_historical_data = lambda *a, **k: next(hids)
    win.show()
    qapp.processEvents()
    return win


def _owners(session) -> int:
    """Active owners: attached views plus the alarm monitor when set."""
    return len(list(session._views)) + (1 if session.monitored else 0)


def _snapshot(win, symbol: str, step: str, rows: list, note: str = "") -> dict:
    session = win._sessions.get(symbol)
    if session is None:
        row = {"step": step, "holders": 0, "owners": 0, "note": note}
    else:
        row = {
            "step": step,
            "holders": int(session._rt_holders),
            "owners": _owners(session),
            "note": note,
        }
    rows.append(row)
    return row


def _decide_verdict(rows: list) -> str:
    """Confirm only when an over-count survives continued session use."""
    live = [r for r in rows if r["step"] != "zero-owner"]
    over = [r for r in live if r["holders"] > r["owners"]]
    if over and live[-1]["holders"] > live[-1]["owners"]:
        return VERDICT_CONFIRMED
    return VERDICT_CLEAN


def _write_record(rows: list, verdict: str) -> None:
    lines = [
        "# P13 hold-count verification record (D49.5 probe — P13-T5)",
        "",
        "Offscreen lifecycle probe (`tests/test_p13_hold_probe.py`,",
        "`QT_QPA_PLATFORM=offscreen`): main-chart load, main-chart",
        "same-symbol reload, pop-out attach, pop-out close, and a zero-owner",
        "case. Hold count is `TickerSession._rt_holders`; active owners are",
        "the session's attached views plus the alarm monitor when it holds",
        "the session. No production file was modified by this probe.",
        "",
        "## Step counts",
        "",
        "| step | hold count | active owners | holds − owners | note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        delta = r["holders"] - r["owners"]
        lines.append(
            f"| {r['step']} | {r['holders']} | {r['owners']} | {delta} "
            f"| {r['note']} |"
        )
    lines += ["", "## Verdict", "", f"Verdict: {verdict}", ""]
    if verdict == VERDICT_CONFIRMED:
        lines += [
            "The probe observed more holds than active owners and the excess",
            "was still present after continued session use (pop-out close),",
            "so the over-count outlives the step that created it.",
        ]
    else:
        lines += [
            "The hold count tracked the active-owner count at every live step",
            "and the zero-owner case returned the count to zero, so no excess",
            "outlives the step that created it.",
        ]
    lines += [""]
    RECORD_PATH.write_text("\n".join(lines), encoding="utf-8")


def test_p13_hold_lifecycle_probe(monkeypatch, qapp):
    """P13-T5-T51: shared-hold lifecycle probe; always lands with a verdict."""
    rows: list = []
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS

        # Step 1: main-chart load — one view, one hold.
        win.load_chart(SYMBOL, TF)
        qapp.processEvents()
        first = _snapshot(win, SYMBOL, "initial-load", rows,
                          note="main chart only")
        assert first["holders"] == 1
        assert first["owners"] == 1

        # Step 2: main-chart same-symbol reload. A reload that lands while
        # the load's backfill wave is still in flight coalesces into the
        # running wave (P7-W1) instead of re-subscribing; record which path
        # the reload took alongside the counts.
        session = win._sessions.get(SYMBOL)
        wave_in_flight = bool(session is not None
                              and session._history_req_ids)
        win.load_chart(SYMBOL, TF)
        qapp.processEvents()
        reload_note = ("coalesced into running wave"
                       if wave_in_flight else "full reload")
        second = _snapshot(win, SYMBOL, "same-symbol-reload", rows,
                           note=reload_note)
        assert second["owners"] == 1
        assert second["holders"] >= 1

        # Step 3: pop-out attach — one new view, one new hold.
        win._open_popout()
        qapp.processEvents()
        assert len(win._popouts) == 1
        third = _snapshot(win, SYMBOL, "popout-attach", rows,
                          note="main chart + one pop-out")
        assert third["owners"] == second["owners"] + 1
        assert third["holders"] == second["holders"] + 1

        # Step 4: pop-out close — the view and its hold both go away.
        win._popouts[0].close()
        qapp.processEvents()
        assert len(win._popouts) == 0
        fourth = _snapshot(win, SYMBOL, "popout-close", rows,
                           note="main chart only again")
        assert fourth["owners"] == third["owners"] - 1
        assert fourth["holders"] == third["holders"] - 1

        # Step 5: zero-owner case — move the main chart away so the SYMBOL
        # session has no views and no monitor; assert the hold count is zero.
        win.load_chart(OTHER, TF)
        qapp.processEvents()
        leftover = win._sessions.get(SYMBOL)
        if leftover is None:
            rows.append({"step": "zero-owner", "holders": 0, "owners": 0,
                         "note": "session torn down"})
        else:
            _snapshot(win, SYMBOL, "zero-owner", rows,
                      note="session retained")
            assert leftover._rt_holders == 0
            assert leftover.rt_req_id is None
        assert rows[-1]["holders"] == 0
        assert rows[-1]["owners"] == 0

        verdict = _decide_verdict(rows)
        assert verdict in (VERDICT_CONFIRMED, VERDICT_CLEAN)
        _write_record(rows, verdict)
    finally:
        win.close()


def test_p13_hold_record_committed():
    """P13-T5-T52: the verification record exists with counts and verdict."""
    assert RECORD_PATH.exists(), "probe record was not committed"
    text = RECORD_PATH.read_text(encoding="utf-8")
    for step in ("initial-load", "same-symbol-reload", "popout-attach",
                 "popout-close", "zero-owner"):
        assert step in text, f"record is missing step {step}"
    # Per-step counts: each step row carries three integers
    # (holders, owners, delta).
    for step in ("initial-load", "same-symbol-reload", "popout-attach",
                 "popout-close", "zero-owner"):
        assert re.search(rf"\| {step} \| \d+ \| \d+ \| -?\d+ \|", text), \
            f"record is missing hold/owner counts for {step}"
    verdicts = re.findall(r"^Verdict: (.+)$", text, re.MULTILINE)
    assert len(verdicts) == 1, "record must carry exactly one verdict line"
    assert verdicts[0].strip() in (VERDICT_CONFIRMED, VERDICT_CLEAN), \
        "verdict vocabulary must be exactly one of the two outcomes"
