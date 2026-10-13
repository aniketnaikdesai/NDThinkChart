"""D39 — symbol search + volume-burst alerts (AC-D39.1–AC-D39.5)."""

from __future__ import annotations

import pytest
from PyQt6.QtCore import QObject, pyqtSignal

from data.alarm_store import AlarmStore
from data.models import Alarm, Bar
from services.alarm_service import evaluate_volume_burst
from services.symbol_search import SymbolSearchService, MAX_SAMPLES
from services.volume_baseline import (
    DEFAULT_Z_THRESHOLD,
    MIN_WARMUP_BARS,
    N_BASELINE_BARS,
    bucket_for_ts,
    mad,
    median,
    minutes_for_timeframe,
    robust_z,
    VolumeBaselineService,
)

BASE_TS = 1_760_000_000  # fixed epoch; buckets derived, not wall-clock


def _bar(ts, volume, timeframe="1 min", symbol="AAPL", price=100.0):
    return Bar(symbol=symbol, timeframe=timeframe, ts=ts, open=price,
               high=price, low=price, close=price, volume=volume)


def _burst_alarm(symbol="AAPL", z_threshold=4.0, **kw):
    params = {"z_threshold": z_threshold, "n": N_BASELINE_BARS}
    params.update(kw.pop("params_extra", {}))
    return Alarm(id=None, symbol=symbol, price=0.0, direction="burst",
                 kind="volume_burst", params=params, **kw)


def _desc(symbol, sec_type="STK", exchange="SMART"):
    from ibapi.contract import ContractDescription
    d = ContractDescription()
    d.contract.symbol = symbol
    d.contract.secType = sec_type
    d.contract.exchange = exchange
    return d


def _clear(symbol: str) -> None:
    from data.db import db
    db.conn.execute("DELETE FROM alarms WHERE symbol=?", (symbol,))
    db.conn.commit()


# ── Pure statistics: robust z-score, never mean/stddev ──────────────────

def test_robust_stats_skew_resistant():
    """One huge outlier must not move the median (mean would)."""
    xs = [100.0] * 29 + [10_000.0]
    assert median(xs) == 100.0
    assert mad(xs, 100.0) == 0.0
    assert sum(xs) / len(xs) > 400  # mean is dragged; median is not


def test_robust_z_flat_baseline_burst_is_finite_and_large():
    """Flat (zero-MAD) baseline: burst → finite z above threshold (AC-D39.3)."""
    z = robust_z(5000.0, 1000.0, 0.0)
    assert z > DEFAULT_Z_THRESHOLD
    assert z < float("inf")


def test_robust_z_flat_data_never_fires():
    assert robust_z(1000.0, 1000.0, 0.0) == 0.0
    assert robust_z(1000.0, 1000.0, 25.0) == 0.0


def test_bucket_for_ts_deterministic():
    assert bucket_for_ts(BASE_TS) == bucket_for_ts(BASE_TS + 86400)
    assert bucket_for_ts(BASE_TS + 60) == (bucket_for_ts(BASE_TS) + 1) % 1440


def test_minutes_for_timeframe():
    assert minutes_for_timeframe("1 min") == 1.0
    assert minutes_for_timeframe("5 mins") == 5.0
    assert minutes_for_timeframe("1 day") == 390.0


# ── VolumeBaselineService: three tiers + guards ──────────────────────────

def test_baseline_warmup_gap_is_documented_not_silent():
    svc = VolumeBaselineService()
    for i in range(MIN_WARMUP_BARS - 1):
        svc.record("AAPL", BASE_TS + i * 86400, "1 min", 1000.0)
    assert svc.baseline("AAPL", BASE_TS) is None
    status = svc.status("AAPL", BASE_TS)
    assert "warming up" in status


def test_baseline_tod_after_warmup():
    svc = VolumeBaselineService()
    for i in range(6):
        svc.record("AAPL", BASE_TS + i * 86400, "1 min", 1000.0 + i * 10)
    med, mad_v, n, source = svc.baseline("AAPL", BASE_TS)
    assert source == "tod"
    assert n == 6
    assert med == pytest.approx(1025.0)  # median of 1000..1050


def test_baseline_rolling_fallback_until_buckets_fill():
    """Tier 3: <5 samples in any one bucket → last-30 rolling window."""
    svc = VolumeBaselineService()
    for i in range(6):  # every bar lands in a different bucket
        svc.record("AAPL", BASE_TS + i * 3600, "1 min", 1000.0)
    med, mad_v, n, source = svc.baseline("AAPL", BASE_TS + 99 * 3600)
    assert source == "rolling"
    assert med == pytest.approx(1000.0)


def test_baseline_volume_floor_on_illiquid_names():
    svc = VolumeBaselineService()
    for i in range(6):
        svc.record("DUST", BASE_TS + i * 86400, "1 min", 0.0)
    assert svc.baseline("DUST", BASE_TS) is None  # no divide-by-noise


def test_baseline_persists_across_instances():
    svc = VolumeBaselineService()
    for i in range(6):
        svc.record("AAPL", BASE_TS + i * 86400, "1 min", 1000.0)
    svc2 = VolumeBaselineService()  # fresh — loads the DB rows
    med, mad_v, n, source = svc2.baseline("AAPL", BASE_TS)
    assert n == 6 and source == "tod" and med == pytest.approx(1000.0)


def test_baseline_never_compares_across_contracts_c39_2():
    """Roll isolation: ESZ5 volume is never judged against an ESH7 baseline."""
    svc = VolumeBaselineService()
    for i in range(6):
        svc.record("ESZ6", BASE_TS + i * 86400, "1 min", 5000.0)
    assert svc.baseline("ESH7", BASE_TS) is None
    svc.invalidate("ESZ6")
    assert svc.baseline("ESZ6", BASE_TS) is None  # in-memory dropped on roll


def test_prime_from_bars_is_one_time():
    svc = VolumeBaselineService()
    bars = [_bar(BASE_TS + i * 86400, 2000.0) for i in range(10)]
    assert svc.prime_from_bars("AAPL", bars) == 10
    assert svc.prime_from_bars("AAPL", bars) == 0  # one-time per key
    med, mad_v, n, source = svc.baseline("AAPL", BASE_TS)
    assert n == 10 and source == "tod"


def test_service_evaluate_fires_and_reports_z():
    svc = VolumeBaselineService()
    for i in range(10):
        svc.record("AAPL", BASE_TS + i * 86400, "1 min", 1000.0)
    fired, z = svc.evaluate("AAPL", BASE_TS, 6000.0, z_threshold=4.0)
    assert fired and z is not None and z >= 4.0
    fired2, z2 = svc.evaluate("AAPL", BASE_TS, 1000.0, z_threshold=4.0)
    assert not fired2 and z2 == pytest.approx(0.0)
    assert svc.evaluate("WARM", BASE_TS, 99999.0) == (False, None)


# ── evaluate_volume_burst ────────────────────────────────────────────────

def test_evaluate_volume_burst_fires_with_z():
    alarm = _burst_alarm()
    fired = evaluate_volume_burst(6000.0, (1000.0, 0.0, 30, "tod"), [alarm])
    assert fired == [alarm]
    assert alarm.trigger_z is not None and alarm.trigger_z >= 4.0


def test_evaluate_volume_burst_flat_never_fires():
    alarm = _burst_alarm()
    assert evaluate_volume_burst(1000.0, (1000.0, 50.0, 30, "tod"), [alarm]) == []


def test_evaluate_volume_burst_warming_up_and_price_ignored():
    burst = _burst_alarm()
    price = Alarm(id=None, symbol="AAPL", price=100.0, direction="cross_above")
    assert evaluate_volume_burst(99999.0, None, [burst]) == []  # warm-up: silent
    assert evaluate_volume_burst(99999.0, None, [price]) == []
    # Price alarms are never evaluated here, even with a baseline.
    assert evaluate_volume_burst(
        99999.0, (1000.0, 10.0, 30, "tod"), [price]) == []


def test_evaluate_volume_burst_threshold_tunable_c39_1():
    """Z-score semantics throughout — no K-multiple language."""
    strict = _burst_alarm(z_threshold=100.0)
    base = (1000.0, 0.0, 30, "tod")
    assert evaluate_volume_burst(6000.0, base, [strict]) == []  # below 100
    loose = _burst_alarm(z_threshold=1.0)
    assert len(evaluate_volume_burst(6000.0, base, [loose])) == 1


def test_evaluate_volume_burst_skips_triggered_and_inactive():
    base = (1000.0, 0.0, 30, "tod")
    done = _burst_alarm()
    done.triggered = True
    assert evaluate_volume_burst(60000.0, base, [done]) == []
    off = _burst_alarm()
    off.active = False
    assert evaluate_volume_burst(60000.0, base, [off]) == []


def test_evaluate_volume_burst_bad_threshold_falls_back_to_default():
    alarm = _burst_alarm()
    alarm.params["z_threshold"] = "nonsense"
    fired = evaluate_volume_burst(6000.0, (1000.0, 0.0, 30, "tod"), [alarm])
    assert len(fired) == 1  # default threshold applied


# ── SymbolSearchService (AC-D39.1, AC-D39.2) ─────────────────────────────

class _FakeBridge(QObject):
    symbol_samples = pyqtSignal(int, object)
    error_msg = pyqtSignal(int, int, str)


class _FakeMD:
    def __init__(self):
        self.calls: list[str] = []

    def req_matching_symbols(self, pattern: str) -> int:
        self.calls.append(pattern)
        return 1000 + len(self.calls)


def _search_svc(debounce_ms=300):
    bridge = _FakeBridge()
    md = _FakeMD()
    svc = SymbolSearchService(md, bridge, debounce_ms=debounce_ms)
    return svc, bridge, md


def _collect(svc):
    got = []
    svc.search_finished.connect(lambda *a: got.append(a))
    return got


def test_ac_d39_2_debounce_limits_requests(qapp):
    """10 keystrokes in 500ms → ≤2 reqMatchingSymbols (one per window)."""
    svc, _bridge, md = _search_svc()
    for i in range(10):
        svc.type_ahead("A" * (i + 1))
    svc._fire()  # debounce expiry
    assert len(md.calls) == 1
    assert md.calls[0] == "AAAAAAAAAA"  # only the final text is searched


def test_search_second_window_issues_second_request(qapp):
    svc, _bridge, md = _search_svc()
    svc.type_ahead("AA")
    svc._fire()
    svc.type_ahead("AAPL")
    svc._fire()
    assert md.calls == ["AA", "AAPL"]


def test_ac_d39_1_samples_capped_at_16(qapp):
    """AC-D39.1: ≤16 samples returned for a pattern."""
    svc, bridge, _md = _search_svc()
    got = _collect(svc)
    svc.type_ahead("AA")
    svc._fire()
    bridge.symbol_samples.emit(1001, [_desc(f"AA{i}") for i in range(20)])
    assert len(got) == 1
    req_id, pattern, ok, samples = got[0]
    assert ok and pattern == "AA"
    assert len(samples) == MAX_SAMPLES == 16


def test_search_empty_pattern_issues_nothing(qapp):
    """Clearing the box fires no request and emits nothing (panel clears)."""
    svc, _bridge, md = _search_svc()
    got = _collect(svc)
    svc.type_ahead("AA")
    svc.type_ahead("   ")
    svc._fire()  # nothing staged
    assert got == [] and md.calls == []


def test_search_error_rejects_and_late_ignored(qapp):
    svc, bridge, _md = _search_svc()
    got = _collect(svc)
    svc.type_ahead("AA")
    svc._fire()
    bridge.error_msg.emit(1001, 200, "nope")
    assert len(got) == 1 and got[0][2] is False
    # Late/duplicate for a resolved reqId is ignored.
    bridge.symbol_samples.emit(1001, [_desc("AA")])
    assert len(got) == 1
    # Unknown reqIds never resolve anything.
    bridge.error_msg.emit(9999, 200, "unrelated")
    assert len(got) == 1


def test_search_timeout_bounded(qapp):
    svc, _bridge, _md = _search_svc()
    got = _collect(svc)
    svc.type_ahead("AA")
    svc._fire()
    svc.on_timeout(1001)
    assert len(got) == 1
    assert got[0][2] is False and got[0][3] == "timeout"


def test_search_disconnected_refuses(qapp):
    """Disconnected → immediate failure (panel also disables the box)."""
    svc, _bridge, md = _search_svc()
    got = _collect(svc)
    svc.set_connected(False)
    svc.type_ahead("AA")
    assert len(got) == 1 and got[0][2] is False
    assert md.calls == []  # nothing issued


# ── Session wiring: per-push burst evaluation (AC-D39.3) ─────────────────

class _StubStatusBar:
    def showMessage(self, msg, ms=0):
        pass


class _StubHost:
    def __init__(self):
        self.volume_baseline = VolumeBaselineService()
        self.alarm_monitor = None
        self.status_bar = _StubStatusBar()
        self.recorded: list[tuple[str, float]] = []

    def _record_symbol_price(self, symbol, price):
        self.recorded.append((symbol, price))


def _session(qapp, symbol="AAPL"):
    from ui.ticker_session import TickerSession
    return TickerSession(symbol, _StubHost())


def test_ac_d39_3_burst_fires_exactly_once(qapp):
    """Flat volume warms the baseline; a burst bar fires once; flat never."""
    _clear("AAPL")
    try:
        session = _session(qapp)
        alarm_id = AlarmStore.add(_burst_alarm("AAPL", z_threshold=4.0))
        session.reload_alarms()

        fired: list = []
        session.alarm_triggered.connect(
            lambda sym, alarms: fired.append((sym, list(alarms))))
        # 7 flat 1-min bars (completed) → rolling baseline warms up.
        for i in range(7):
            session._on_aggregated_bar(_bar(BASE_TS + i * 60, 1000.0), True)
        assert fired == []  # flat data never fires
        # Burst bar: 8× the baseline volume.
        session._on_aggregated_bar(_bar(BASE_TS + 7 * 60, 8000.0), True)
        assert len(fired) == 1
        sym, alarms = fired[0]
        assert sym == "AAPL" and len(alarms) == 1
        assert alarms[0].trigger_z is not None and alarms[0].trigger_z >= 4.0
        # Persisted as triggered (AC-D39.4 half).
        assert AlarmStore.load("AAPL")[0].triggered
        # Exactly once: a second burst push does not refire.
        session._on_aggregated_bar(_bar(BASE_TS + 8 * 60, 9000.0), True)
        assert len(fired) == 1
        _ = alarm_id
    finally:
        _clear("AAPL")


def test_burst_evaluation_uses_completed_bars_for_baseline(qapp):
    """Forming bars are evaluated but never recorded into the baseline."""
    _clear("AAPL")
    try:
        session = _session(qapp)
        vb = session._volume_baseline
        for i in range(6):
            session._on_aggregated_bar(_bar(BASE_TS + i * 60, 1000.0), True)
        # 5 completed bars recorded (bar0..bar4); the forming bar6 is not.
        assert len(vb._rolling["AAPL"]) == 5
    finally:
        _clear("AAPL")


def test_ac_d39_4_rearm_reenables(qapp):
    _clear("AAPL")
    try:
        session = _session(qapp)
        alarm_id = AlarmStore.add(_burst_alarm("AAPL", z_threshold=4.0))
        session.reload_alarms()
        for i in range(7):
            session._on_aggregated_bar(_bar(BASE_TS + i * 60, 1000.0), True)
        session._on_aggregated_bar(_bar(BASE_TS + 7 * 60, 8000.0), True)
        assert AlarmStore.load("AAPL")[0].triggered
        AlarmStore.rearm(alarm_id)
        reloaded = AlarmStore.load("AAPL")[0]
        assert reloaded.active and not reloaded.triggered
    finally:
        _clear("AAPL")


# ── Headless monitor + index proxy (AC-D39.4, 39.4) ──────────────────────

def _make_window(monkeypatch, qapp):
    from ibkr.client import IBApiClient

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    from ui.main_window import MainWindow

    win = MainWindow()
    ids = iter([5001, 5002, 5003, 5004, 5005])
    win.rt_manager.subscribe = lambda *a, **k: next(ids)
    win.md_manager.req_historical_data = lambda *a, **k: 5999
    win.show()
    qapp.processEvents()
    return win


def test_ac_d39_4_headless_monitor_includes_burst(monkeypatch, qapp):
    """A burst alarm keeps its symbol in the headless monitored set."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear("HEADA")
        AlarmStore.add(_burst_alarm("HEADA", z_threshold=4.0))
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        session = win._sessions.get("HEADA")
        assert session is not None and session.monitored
        assert any(a.kind == "volume_burst" for a in session._alarms)
    finally:
        _clear("HEADA")
        win.close()


def test_proxy_spx_burst_uses_es_session(monkeypatch, qapp):
    """39.4: SPX burst alarm → ES session ensured; no SPX session; ES-tape label."""
    win = _make_window(monkeypatch, qapp)
    try:
        _clear("SPX")
        AlarmStore.add(_burst_alarm(
            "SPX", z_threshold=4.0,
            params_extra={"proxy": "ES", "proxy_label": "ES tape"}))
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        assert "ES" in win._sessions
        assert "SPX" not in win._sessions  # indices have no tape — no session
        es = win._sessions["ES"]
        proxied = [a for a in es._alarms
                   if a.kind == "volume_burst" and a.symbol == "SPX"]
        assert len(proxied) == 1
        # The alarm toast line names the proxy tape.
        line = win._alarm_toast_line(proxied[0])
        assert "ES tape" in line
    finally:
        _clear("SPX")
        win.close()


def test_proxy_released_when_alarm_deleted(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        _clear("SPX")
        alarm_id = AlarmStore.add(_burst_alarm(
            "SPX", params_extra={"proxy": "ES", "proxy_label": "ES tape"}))
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        assert "ES" in win._sessions
        AlarmStore.delete(alarm_id)
        win.alarm_monitor.reconcile()
        qapp.processEvents()
        es = win._sessions.get("ES")
        assert es is None or not es.monitored
    finally:
        _clear("SPX")
        win.close()


# ── Search select → contract resolution → load_chart (AC-D39.1) ──────────

def test_ac_d39_1_select_loads_chart(monkeypatch, qapp):
    win = _make_window(monkeypatch, qapp)
    try:
        win._ibkr_connected = True
        desc = _desc("AAPL")

        def fake_request(symbol, contract):
            win._pending_search_select[4242] = desc
            return 4242

        win._contract_lookup.request = fake_request
        loaded: list[str] = []
        win.load_chart = lambda symbol, **k: loaded.append(symbol)

        win._on_search_sample_selected(desc)
        assert 4242 in win._pending_search_select
        win._on_search_sample_validated(4242, True, "ok")
        assert loaded == ["AAPL"]

        # Failed resolution → status message, no chart load.
        win._pending_search_select[4243] = desc
        win._on_search_sample_validated(4243, False, "no_contract_details")
        assert loaded == ["AAPL"]
    finally:
        win.close()


def test_search_panel_results_popup(qapp):
    from ui.watchlist_panel import WatchlistPanel
    panel = WatchlistPanel()
    try:
        got: list = []
        panel.search_sample_selected.connect(got.append)
        panel.show_search_results([_desc("AAPL"), _desc("AA")])
        assert panel._search_list.count() == 2
        assert "AAPL" in panel._search_list.item(0).text()
        panel._on_search_item_clicked(panel._search_list.item(0))
        assert len(got) == 1 and got[0].contract.symbol == "AAPL"
        # Empty results → clear "No matches" state, not a crash.
        panel.show_search_results([])
        assert panel._search_list.count() == 1
        assert panel._search_list.item(0).text() == "No matches"
    finally:
        panel.clear_search_results()
        panel.close()


def test_search_box_disabled_while_disconnected(qapp):
    from ui.watchlist_panel import WatchlistPanel
    panel = WatchlistPanel()
    try:
        panel.set_search_enabled(False)
        assert not panel.search_box.isEnabled()
        panel.set_search_enabled(True)
        assert panel.search_box.isEnabled()
    finally:
        panel.close()


# ── Alarm dialog: burst creation + proxy attribution ─────────────────────

def test_alarm_dialog_creates_burst_alarm(qapp):
    from ui.alarm_dialog import AlarmDialog
    _clear("AAPL")
    try:
        dlg = AlarmDialog("AAPL", 100.0)
        dlg.kind_input.setCurrentText("Volume burst")
        dlg.z_input.setValue(6.0)
        dlg._add_alarm()
        bursts = [a for a in AlarmStore.load("AAPL")
                  if a.kind == "volume_burst"]
        assert len(bursts) == 1
        assert bursts[0].params["z_threshold"] == 6.0
        assert bursts[0].price == 0.0
        dlg.close()
    finally:
        _clear("AAPL")


def test_alarm_dialog_burst_on_index_sets_proxy(qapp):
    from ui.alarm_dialog import AlarmDialog
    _clear("SPX")
    try:
        dlg = AlarmDialog("SPX", 6000.0)
        dlg.kind_input.setCurrentText("Volume burst")
        dlg._add_alarm()
        bursts = [a for a in AlarmStore.load("SPX")
                  if a.kind == "volume_burst"]
        assert len(bursts) == 1
        assert bursts[0].params["proxy"] == "ES"
        assert bursts[0].params["proxy_label"] == "ES tape"
        dlg.close()
    finally:
        _clear("SPX")


# ── Chart overlay ignores burst alarms (no bogus line at zero) ───────────

def test_alarm_overlay_skips_burst_alarms(qapp):
    from ui.alarm_overlay import AlarmOverlay
    from ui.chart_panel import ChartPanel
    panel = ChartPanel()
    try:
        overlay = AlarmOverlay(panel.price_plot)
        price_alarm = Alarm(id=1, symbol="AAPL", price=100.0,
                            direction="cross_above")
        burst = _burst_alarm("AAPL")
        burst.id = 2
        overlay.set_data([price_alarm, burst])
        assert overlay.alarm_count() == 1  # only the price alarm draws
    finally:
        panel.close()


# ── Owner rule: no mock endpoint of any kind in production code ──────────

def test_ac_d39_production_tree_has_no_mock_endpoint():
    """Owner rule: mocked/faked/stubbed endpoints exist ONLY in tests."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    for sub in ("ibkr", "services", "ui", "data"):
        for path in (root / sub).rglob("*.py"):
            lowered = path.read_text().lower()
            assert "fakeclient" not in lowered, path
            assert "mockclient" not in lowered, path
            assert "stubclient" not in lowered, path
            assert "simulatedclient" not in lowered, path
            assert "fakeserver" not in lowered, path
            assert "mockserver" not in lowered, path
