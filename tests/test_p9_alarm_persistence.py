"""P9-T1 — alarm persistence isolation (S-P9-3): fault-injection repro + retry.

Repro-first: T11/T12 fail on the pre-fix tree (an injected mark_triggered
DB failure aborts the bar path — no emit, triggered unset, _last_chart_price
stalled) and pass once both call sites in ui/ticker_session.py isolate the
failure (log with symbol/alarm context, still set triggered, still emit,
still advance the price, queue the ID for retry).

T13 proves the retry queue drains on a subsequent bar and on reload_alarms
with no duplicate emissions. T14 proves the error log carries symbol plus
alarm-ID context.
"""

from __future__ import annotations

import logging
import types

import ui.ticker_session as ts_mod
from data.alarm_store import AlarmStore
from data.models import Alarm, Bar

SYM = "P9T1A"
SYM_BURST = "P9T1B"
SYM_RETRY = "P9T1C"
TF = "1m"
BASE_TS = 1_760_000_000


def _clear(symbol: str) -> None:
    from data.db import db

    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.commit()


def _stub_host():
    """Minimal host: only what the bar path touches."""
    return types.SimpleNamespace(_record_symbol_price=lambda *a: None)


def _make_session(qapp, symbol: str):
    return ts_mod.TickerSession(symbol, _stub_host())


def _bar(symbol: str, close: float, ts: int = BASE_TS) -> Bar:
    return Bar(symbol, TF, ts, close - 0.1, close + 0.1, close - 0.2,
               close, 100.0)


def _price_alarm(symbol: str, price: float = 100.5,
                 aid: int | None = 900001) -> Alarm:
    return Alarm(id=aid, symbol=symbol, price=price,
                 direction="cross_above", active=True, sound=False)


def _boom(alarm_id: int, triggered_at: int | None = None) -> None:
    raise RuntimeError("injected persistence failure")


def test_p9_t1_t11_price_path_isolated(monkeypatch, qapp):
    """T11: injected mark_triggered failure on the _on_aggregated_bar path —
    emit still fires, triggered still set, price still advances."""
    session = _make_session(qapp, SYM)
    try:
        alarm = _price_alarm(SYM)
        session.set_alarms([alarm])
        session._last_chart_price = 100.0
        emitted: list = []
        session.alarm_triggered.connect(
            lambda sym, alarms: emitted.append((sym, list(alarms))))
        monkeypatch.setattr(AlarmStore, "mark_triggered", _boom)

        session._on_aggregated_bar(_bar(SYM, 101.0), True)

        assert alarm.triggered is True
        assert len(emitted) == 1 and emitted[0][0] == SYM
        assert session._last_chart_price == 101.0
    finally:
        session.deleteLater()


def test_p9_t1_t12_burst_path_isolated(monkeypatch, qapp):
    """T12: injected mark_triggered failure on the _evaluate_burst_alarms
    path — emit still fires, triggered still set, price still advances."""
    session = _make_session(qapp, SYM_BURST)
    try:
        alarm = Alarm(id=900002, symbol=SYM_BURST, price=99999.0,
                       direction="cross_above", active=True, sound=False,
                       kind="volume_burst")
        session.set_alarms([alarm])
        session._last_chart_price = 50.0
        # Isolate the SUT (persistence handling) from baseline math: the
        # burst evaluation itself fires for the lone burst alarm.
        monkeypatch.setattr(
            ts_mod, "evaluate_volume_burst",
            lambda per_min, baseline, alarms: list(alarms))
        monkeypatch.setattr(AlarmStore, "mark_triggered", _boom)
        emitted: list = []
        session.alarm_triggered.connect(
            lambda sym, alarms: emitted.append((sym, list(alarms))))

        session._on_aggregated_bar(_bar(SYM_BURST, 50.5), True)

        assert alarm.triggered is True
        assert len(emitted) == 1 and emitted[0][0] == SYM_BURST
        assert session._last_chart_price == 50.5
    finally:
        session.deleteLater()


def test_p9_t1_t13_retry_flushes_no_dupes(monkeypatch, qapp):
    """T13: fail once, restore, drive a subsequent bar + reload_alarms —
    the queue drains with exactly one emission total."""
    _clear(SYM_RETRY)
    session = _make_session(qapp, SYM_RETRY)
    try:
        aid = AlarmStore.add(_price_alarm(SYM_RETRY, aid=None))
        alarm = _price_alarm(SYM_RETRY, aid=aid)
        session.set_alarms([alarm])
        session._last_chart_price = 100.0
        emitted: list = []
        session.alarm_triggered.connect(
            lambda sym, alarms: emitted.append((sym, list(alarms))))
        orig = AlarmStore.mark_triggered
        monkeypatch.setattr(AlarmStore, "mark_triggered", _boom)

        session._on_aggregated_bar(_bar(SYM_RETRY, 101.0), True)

        assert alarm.triggered is True
        assert len(emitted) == 1
        assert session._trigger_retry_queue == [aid]

        # DB recovers: the next bar flushes the retry.
        monkeypatch.setattr(
            AlarmStore, "mark_triggered", staticmethod(orig))
        session._on_aggregated_bar(
            _bar(SYM_RETRY, 102.0, ts=BASE_TS + 60), True)

        assert session._trigger_retry_queue == []
        assert len(emitted) == 1

        session.reload_alarms()

        assert session._trigger_retry_queue == []
        assert len(emitted) == 1
        assert AlarmStore.load(SYM_RETRY)[0].triggered is True
    finally:
        _clear(SYM_RETRY)
        session.deleteLater()


def test_p9_t1_t14_error_log_carries_context(monkeypatch, qapp, caplog):
    """T14: the caught persistence failure logs the symbol + alarm ID."""
    session = _make_session(qapp, SYM)
    try:
        alarm = _price_alarm(SYM, aid=900014)
        session.set_alarms([alarm])
        session._last_chart_price = 100.0
        monkeypatch.setattr(AlarmStore, "mark_triggered", _boom)

        with caplog.at_level(logging.ERROR, logger="ui.ticker_session"):
            session._on_aggregated_bar(_bar(SYM, 101.0), True)

        assert alarm.triggered is True
        hits = [r for r in caplog.records
                if r.levelno >= logging.ERROR
                and SYM in r.getMessage()
                and "900014" in r.getMessage()]
        assert hits, "expected an error log naming symbol + alarm ID"
    finally:
        session.deleteLater()
