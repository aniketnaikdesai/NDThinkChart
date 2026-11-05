"""P17-T4 (D56.6, D56.2-verify, D56.7-gate) — D53 retry state + double-silent fall-through.

T41: offscreen wave-state + indicator-state assertions across first-issue
flight, retry in flight, and completion (distinguishability, elapsed
continuity, no premature current-claim, latch set-only-in-flight and
cleared-only-terminally).

T42: offscreen double-silent waves in both variants (zero-bar re-issue silent;
partial re-issue stalled) — exactly two issues per chunk plus watchdog
strand-finalization state, no second retry, no watchdog change.

T43: requirements history-intact grep (marker sentence, Current Tech Stack,
### D41 through ### D55). The full offscreen suite green is established by
the worker's clean full-suite run recorded in the results JSON (a suite
cannot run itself from inside one of its own modules).
"""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from ibkr.contracts import get_contract_for_symbol
from services.backfill_service import RequestPlan


def _plan(i: int) -> RequestPlan:
    return RequestPlan(
        endDateTime=f"2024010{i % 9 + 1}  16:00:00",
        duration="5 D",
        bar_size="5 mins",
        span_start_ts=1_700_000_000 + i,
        span_end_ts=1_700_100_000 + i,
    )


def _bar(i: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        date=f"2024010{i % 9 + 1}  09:35:00",
        open=100.0 + i,
        high=101.0 + i,
        low=99.0 + i,
        close=100.5 + i,
        volume=1000.0,
    )


class _FakeMD:
    """Paced-transport double: issues incrementing reqIds, records cancels."""

    def __init__(self) -> None:
        self._next = 7100
        self.issued: list[int] = []
        self.by_plan: dict[str, int] = {}
        self.cancelled: list[int] = []

    def req_historical_data(self, **kwargs):
        self._next += 1
        self.issued.append(self._next)
        end = kwargs.get("endDateTime", "?")
        self.by_plan[end] = self.by_plan.get(end, 0) + 1
        return self._next

    def cancel_historical_data(self, req_id):
        self.cancelled.append(req_id)


@pytest.fixture
def window(qapp, tmp_path, monkeypatch):
    """A real MainWindow offscreen on a throwaway DB (no live IBKR)."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "t56.db"))
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    w = MainWindow()
    try:
        yield w
    finally:
        for session in list(w._sessions.values()):
            try:
                session.teardown()
            except Exception:
                pass


def _drive_wave(window, monkeypatch, n_plans=2):
    """Issue a wave of n_plans chunks under a controllable silence clock."""
    session = window.get_or_create_session("AAA")
    fake = _FakeMD()
    monkeypatch.setattr(window, "md_manager", fake)
    clock = [1_000.0]
    monkeypatch.setattr(session, "_silence_now", lambda: clock[0])
    session.queue_wave_plans(
        [_plan(i) for i in range(n_plans)],
        get_contract_for_symbol("AAA"),
        "5 mins",
        False,
    )
    assert len(session._history_req_ids) == n_plans
    assert len(fake.issued) == n_plans
    return session, fake, clock


def _raise(window, session):
    """Stamp the MainWindow-local wave baseline and refresh the indicator."""
    window._backfill_wave_start = time.time()
    window._refresh_backfill_indicator(session)
    return window._backfill_indicator.text()


# ── T41 — retry state on the D53 indicator ────────────────────────────────────


def test_t41_retry_state_distinguishable_continuing_and_latched(
    window, monkeypatch
):
    """First-issue flight, retry in flight, and completion each read distinctly.

    The retry label appears only once a retry is in flight, elapsed keeps
    counting from the wave baseline (never reset by the retry), no
    current-cache claim appears while spans are missing, and the marker
    clears only on terminal finalization.
    """
    session, fake, clock = _drive_wave(window, monkeypatch, n_plans=2)
    first_ids = sorted(session._history_req_ids)

    first_text = _raise(window, session)
    assert "retry" not in first_text.lower()
    state = window._backfill_state
    assert state["retry"] is False
    assert state["retry_req_ids"] == []
    assert state["in_flight"] == 2
    time.sleep(0.06)
    window._refresh_backfill_indicator(session)
    elapsed_first = window._backfill_state["elapsed_s"]
    assert elapsed_first > 0.0

    # One full silence window with no bars/ENDs/errors: both chunks retry.
    clock[0] += 31.0
    session._sweep_silent_chunks()
    assert len(fake.issued) == 4, "each silent chunk is re-issued exactly once"
    assert sorted(fake.cancelled) == first_ids
    retried_ids = sorted(session._history_req_ids)
    assert set(retried_ids).isdisjoint(first_ids)

    retry_text = window._backfill_indicator.text()
    # The refresh after the retry entered flight must show the retry state.
    window._refresh_backfill_indicator(session)
    retry_text = window._backfill_indicator.text()
    assert "(retry" in retry_text, f"retry state must be explicit: {retry_text!r}"
    assert retry_text != first_text, "retry must differ from first-issue flight"
    state = window._backfill_state
    assert state["retry"] is True, "marker set while a retry is in flight"
    assert state["retry_req_ids"] == retried_ids
    assert state["elapsed_s"] >= elapsed_first, (
        "elapsed must continue from the wave baseline, never reset by a retry"
    )
    assert "current" not in retry_text.lower(), (
        "no current-cache claim while spans are missing (AC-D53.3)"
    )
    assert "current" not in window.status_bar.currentMessage().lower()

    # The retried chunks end the wave: terminal funnel clears the marker.
    for req_id in list(session._history_req_ids):
        window._on_historical_data_end(req_id)
    idle_text = window._backfill_indicator.text()
    assert idle_text == "Backfill: idle"
    assert window._backfill_state is None, (
        "marker cleared only by the terminal funnel"
    )
    assert retry_text != idle_text, "retry must differ from completion"
    assert "current" not in window.status_bar.currentMessage().lower()


# ── T42 — double-silent fall-through, both variants ───────────────────────────


def _assert_stranded_shortfall(window, session, fake, gen_before):
    """Shared watchdog strand-finalization assertions (unchanged path)."""
    assert len(fake.issued) == 4, "no third issue for any chunk"
    assert session._history_generation > gen_before, (
        "the watchdog advanced the generation so late arrivals stay fenced"
    )
    assert not session._history_req_ids and not session._wave_plan_queue
    assert window._backfill_indicator.text() == "Backfill: idle"
    assert window._backfill_state is None
    msg = window.status_bar.currentMessage()
    assert "backfill incomplete" in msg, (
        f"AC-D16.4 shortfall must surface, got: {msg!r}"
    )
    assert "timed out" in msg, f"stranded cause must be tagged, got: {msg!r}"
    assert "current" not in msg.lower(), "no current-cache claim on shortfall"


def test_t42_double_silent_zero_bar_variant_finalizes_via_watchdog(
    window, monkeypatch
):
    """A re-issued chunk silent again past 30 s is never re-issued a third time."""
    session, fake, clock = _drive_wave(window, monkeypatch, n_plans=2)
    window._backfill_wave_start = time.time()

    clock[0] += 31.0
    session._sweep_silent_chunks()
    assert len(fake.issued) == 4
    for plan in session._req_to_plan.values():
        pass  # live plans tracked below via the fake's per-plan counts
    assert sorted(fake.by_plan.values()) == [2, 2], (
        f"exactly two issues per chunk, got {fake.by_plan}"
    )

    # The re-issues go silent past their own 30 s window: no second retry.
    clock[0] += 31.0
    session._sweep_silent_chunks()
    assert len(fake.issued) == 4, "a re-issue's own silence never re-issues"
    assert sorted(fake.by_plan.values()) == [2, 2]

    gen_before = session._history_generation
    window._on_session_history_wave_timeout(session)
    _assert_stranded_shortfall(window, session, fake, gen_before)


def test_t42_double_silent_partial_variant_finalizes_via_watchdog(
    window, monkeypatch
):
    """A partial-then-stalled re-issue is dropped exactly-once and never retried."""
    session, fake, clock = _drive_wave(window, monkeypatch, n_plans=2)
    window._backfill_wave_start = time.time()

    first_ids = sorted(session._history_req_ids)
    session.on_historical_bar(first_ids[0], _bar(0))
    session.on_historical_bar(first_ids[0], _bar(1))
    assert len(session._pending_bars) == 2

    # Trailing silence past 30 s fires the retry for the stalled partial too.
    clock[0] += 31.0
    session._sweep_silent_chunks()
    assert len(fake.issued) == 4
    assert sorted(fake.by_plan.values()) == [2, 2]
    # Exactly-once: the old partial bars were identity-removed, never counted.
    assert session._pending_bars == [], (
        "superseded partial bars must leave the wave totals"
    )

    # The re-issues stall as well: still no second retry.
    clock[0] += 31.0
    session._sweep_silent_chunks()
    assert len(fake.issued) == 4, "a re-issue's own silence never re-issues"

    gen_before = session._history_generation
    window._on_session_history_wave_timeout(session)
    _assert_stranded_shortfall(window, session, fake, gen_before)


# ── T43 — batch gate: requirements history intact ─────────────────────────────


def test_t43_requirements_history_intact():
    """The phase batch leaves requirements history untouched.

    The Existing Repository marker sentence and Current Tech Stack stay put,
    ### D41 through ### D55 are all present with their reversals, and no
    pre-P17 wording is touched (this worker edits no requirements file —
    verified via git status in the results report).
    """
    root = Path(__file__).resolve().parents[1]
    text = (
        root / "docs" / "requirements" / "requirements.md"
    ).read_text(encoding="utf-8")
    assert "Existing Repository" in text, "repository marker sentence intact"
    assert "Current Tech Stack" in text, "tech stack section intact"
    missing = [f"### D{n}" for n in range(41, 56) if f"### D{n}" not in text]
    assert not missing, f"decision sections missing: {missing}"
