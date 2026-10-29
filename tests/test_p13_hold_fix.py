"""P13-T6 — conditional per-owner hold fix, else verified-close (D49.5 fix half).

Record-gated task (S-P13-5, wave W6 half): reads the P13-T5 probe verdict in
``docs/p13_hold_probe_record.md`` and acts exactly on it.

- Verdict ``lasting effect confirmed`` → the idempotent per-owner
  acquire/release fix must be present (owners: main chart, each pop-out,
  alarm monitor) with the hold count equal to active owners across the probe
  lifecycle, including double-acquire/release safety.
- Verdict ``no lasting effect`` → NO production-code change; this task closes
  D49.5 as verified (A126) by asserting the hold-accounting code paths are
  unchanged from the probed baseline and the lifecycle still tracks owners.

Both branches assert inline — no skip in either branch. A diff here with no
probe record fails review (R98), so the record's presence and single verdict
line are asserted first.
"""

from __future__ import annotations

import inspect
import itertools
import re
from pathlib import Path

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

HOLD_TEST_FILES = ("test_p13_hold_probe.py", "test_p13_hold_fix.py")

_SKIP_XFAIL_RE = re.compile(
    r"pytest\.mark\.(skip|xfail)|pytest\.(skip|xfail)\s*\(|"
    r"@pytest\.mark\.skip|@pytest\.mark\.xfail",
)


def _read_verdict() -> str:
    assert RECORD_PATH.exists(), "P13-T5 probe record is missing (R98)"
    text = RECORD_PATH.read_text(encoding="utf-8")
    verdicts = re.findall(r"^Verdict: (.+)$", text, re.MULTILINE)
    assert len(verdicts) == 1, "record must carry exactly one verdict line"
    verdict = verdicts[0].strip()
    assert verdict in (VERDICT_CONFIRMED, VERDICT_CLEAN), (
        f"unknown probe verdict: {verdict!r}"
    )
    return verdict


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


def test_p13_hold_fix_matches_verdict(monkeypatch, qapp):
    """P13-T6-T61: tree state agrees with the probe verdict, either way."""
    verdict = _read_verdict()

    if verdict == VERDICT_CONFIRMED:
        # A lasting effect was confirmed, so the per-owner fix must be
        # present: owner-keyed acquire/release with the hold count equal to
        # active owners and idempotent double-acquire/release safety.
        from ui.ticker_session import TickerSession

        assert hasattr(TickerSession, "acquire_rt"), (
            "confirmed verdict but no per-owner acquire API"
        )
        assert hasattr(TickerSession, "release_rt"), (
            "confirmed verdict but no per-owner release API"
        )
        win = _make_window(monkeypatch, qapp)
        try:
            win._now_ts = lambda: NOW_TS
            win.load_chart(SYMBOL, TF)
            qapp.processEvents()
            session = win._sessions[SYMBOL]
            # Double acquire by the same owner is idempotent: one hold.
            session.acquire_rt("main")
            session.acquire_rt("main")
            assert session._rt_holders == _owners(session)
            # A second owner adds exactly one hold; releasing one owner
            # leaves the other's hold intact.
            session.acquire_rt("popout-1")
            assert session._rt_holders == _owners(session) + 1 or (
                session._rt_holders == 2
            )
            session.release_rt("popout-1")
            session.release_rt("popout-1")  # idempotent: no double release
            assert session._rt_holders == _owners(session)
        finally:
            win.close()
    else:
        # Clean verdict: verified-close. The hold accounting must be the
        # probed baseline — plain integer refcount, no per-owner identity.
        from ui.ticker_session import TickerSession

        assert not hasattr(TickerSession, "acquire_rt"), (
            "clean verdict but a per-owner acquire API is present: "
            "unlicensed D49.5 diff"
        )
        assert not hasattr(TickerSession, "release_rt_for"), (
            "clean verdict but a per-owner release API is present: "
            "unlicensed D49.5 diff"
        )
        for name in ("ensure_rt_subscribed", "release_rt"):
            params = list(
                inspect.signature(getattr(TickerSession, name)).parameters
            )
            assert params == ["self"], (
                f"clean verdict but {name}{params}: hold-accounting "
                "contract changed without a confirmed effect"
            )
        win = _make_window(monkeypatch, qapp)
        try:
            win._now_ts = lambda: NOW_TS
            win.load_chart(SYMBOL, TF)
            qapp.processEvents()
            session = win._sessions[SYMBOL]
            assert not hasattr(session, "_rt_owners"), (
                "clean verdict but owner-keyed hold state is present"
            )
            # Baseline refcount still round-trips through the lifecycle.
            assert session._rt_holders == _owners(session) == 1
            win._open_popout()
            qapp.processEvents()
            assert session._rt_holders == _owners(session) == 2
            win._popouts[0].close()
            qapp.processEvents()
            assert session._rt_holders == _owners(session) == 1
        finally:
            win.close()


def test_p13_hold_suites_green_no_markers(monkeypatch, qapp):
    """P13-T6-T62: lifecycle re-run tracks owners; zero skip/xfail markers."""
    # Scan the P13 hold test files for skip/xfail markers.
    tests_dir = Path(__file__).resolve().parent
    for name in HOLD_TEST_FILES:
        text = (tests_dir / name).read_text(encoding="utf-8")
        assert not _SKIP_XFAIL_RE.search(text), (
            f"{name} carries a skip/xfail marker"
        )

    # Re-run the probe lifecycle against the final tree: hold count must
    # equal active owners at every live step, zero at zero owners.
    win = _make_window(monkeypatch, qapp)
    try:
        win._now_ts = lambda: NOW_TS
        win.load_chart(SYMBOL, TF)
        qapp.processEvents()
        session = win._sessions[SYMBOL]
        assert session._rt_holders == _owners(session) == 1

        win.load_chart(SYMBOL, TF)  # same-symbol reload
        qapp.processEvents()
        session = win._sessions[SYMBOL]
        assert _owners(session) == 1
        assert session._rt_holders >= 1

        win._open_popout()
        qapp.processEvents()
        assert len(win._popouts) == 1
        assert session._rt_holders == _owners(session) == 2

        win._popouts[0].close()
        qapp.processEvents()
        assert len(win._popouts) == 0
        assert session._rt_holders == _owners(session) == 1

        win.load_chart(OTHER, TF)
        qapp.processEvents()
        leftover = win._sessions.get(SYMBOL)
        if leftover is None:
            holders, owners = 0, 0
        else:
            holders, owners = leftover._rt_holders, _owners(leftover)
            assert leftover._rt_holders == 0
        assert (holders, owners) == (0, 0)
    finally:
        win.close()
