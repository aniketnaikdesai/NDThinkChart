"""D36 — footprint charts (P0) acceptance tests.

Covers AC-D36.1–AC-D36.5 at the unit/session/UI level. All IBKR touching
uses a fake client (tests only — production code never sees one). No live
TWS is contacted; nothing here transmits an order.
"""
import sqlite3
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from data.models import Bar
from services.footprint_service import (
    FootprintService,
    PageSpec,
    FormingSpec,
    bucket_bid_ask_levels,
    bucket_trade_levels,
)
from ui.footprint_item import FootprintItem

BASE = 1_760_000_000  # a fixed epoch for deterministic tests


def _bar(ts, timeframe="5 mins"):
    return Bar("ES", timeframe, ts, 100.0, 101.0, 99.0, 100.5, 1000.0)


def _bid_ask(ts, bid, ask, size_bid=10, size_ask=20):
    return SimpleNamespace(time=ts, priceBid=bid, priceAsk=ask,
                           sizeBid=size_bid, sizeAsk=size_ask)


def _trade(ts, price, size):
    return SimpleNamespace(time=ts, price=price, size=size,
                           exchange="", specialConditions="")


def _end_ts(end_str: str) -> int:
    """Parse a PageSpec end_str back to unix seconds (UTC)."""
    return int(datetime.strptime(end_str, "%Y%m%d-%H:%M:%S")
               .replace(tzinfo=timezone.utc).timestamp())


def _backfill_bar_bidask(service, bar_ts, n_pages, page_ticks=1000):
    """Drive n full BID_ASK pages backward; return the page end ts list.

    Callers should use daily bars: 1000 ticks at 1s spacing need a window
    wider than 1000s so the earliest tick stays after the bar start (the
    followup condition).
    """
    service.set_visible_range(bar_ts, bar_ts)
    ends = []
    followup = None
    for page in range(n_pages):
        specs = (service.next_wave(max_requests=1) if page == 0
                 else [followup])
        assert len(specs) == 1, f"page {page}: expected one spec"
        spec = specs[0]
        assert isinstance(spec, PageSpec) and spec.kind == "BID_ASK"
        end = _end_ts(spec.end_str)
        ends.append(end)
        req_id = 1000 + page
        service.note_issued(req_id, spec)
        ticks = [_bid_ask(end - i, 100.0, 100.25) for i in range(page_ticks)]
        result = service.on_ticks_bid_ask(req_id, ticks, done=False)
        followup = result["followup"]
        assert followup is not None, f"page {page}: expected followup"
    return ends


# ── AC-D36.1: bid×ask bucketing, sums and delta ────────────────────────

def test_ac_d36_1_bid_ask_bucket_sums_and_delta():
    ticks = [_bid_ask(BASE + 10, 100.0, 100.25, size_bid=3, size_ask=5),
             _bid_ask(BASE + 20, 100.0, 100.25, size_bid=7, size_ask=1)]
    lv = bucket_bid_ask_levels(ticks, BASE, BASE + 300)
    # Bid volume accrues at the bid price, ask volume at the ask price.
    assert lv[100.0][0] == 10.0      # bid total
    assert lv[100.0][1] == 0.0
    assert lv[100.25][0] == 0.0
    assert lv[100.25][1] == 6.0      # ask total


def test_ac_d36_1_trade_bucket_volume_and_count():
    ticks = [_trade(BASE + 5, 100.5, 4),
             _trade(BASE + 9, 100.5, 6),
             _trade(BASE + 12, 100.75, 2)]
    lv = bucket_trade_levels(ticks, BASE, BASE + 300)
    assert lv[100.5][0] == 10.0      # trade volume
    assert lv[100.5][1] == 2         # trade count
    assert lv[100.75][0] == 2.0
    assert lv[100.75][1] == 1


def test_ac_d36_1_window_filtering_excludes_out_of_range_ticks():
    ticks = [_bid_ask(BASE - 5, 100.0, 100.25),    # before window
             _bid_ask(BASE + 400, 100.0, 100.25)]   # after window
    assert bucket_bid_ask_levels(ticks, BASE, BASE + 300) == {}


# ── AC-D36.2: 1000-tick backward pages, no gaps / overlaps ────────────

def test_ac_d36_2_pages_are_contiguous_with_no_gaps_or_overlaps():
    # Daily bars: 1000 ticks at 1s spacing fit inside one bar window, so a
    # full page always yields a followup. The target is a completed bar
    # (the last bar is forming-only).
    bars = [_bar(BASE + i * 86400, timeframe="1 day") for i in range(2)]
    service = FootprintService("ES")
    service.sync_bars(bars, "1 day")
    target = BASE
    ends = _backfill_bar_bidask(service, target, n_pages=3)
    # Full 1000-tick pages at 1s spacing: page k ends exactly 1000s after
    # page k+1 ends — no gap, no overlap.
    for i in range(len(ends) - 1):
        assert ends[i] - ends[i + 1] == 1000, \
            f"gap/overlap between pages {i} and {i+1}"
    assert service.pending_count() == 1  # TRADES phase still pending


def test_ac_d36_2_full_page_keeps_phase_open():
    bars = [_bar(BASE + i * 86400, timeframe="1 day") for i in range(3)]
    service = FootprintService("ES")
    service.sync_bars(bars, "1 day")
    target = BASE
    spec = service.next_wave(max_requests=1)[0]
    service.note_issued(42, spec)
    end = _end_ts(spec.end_str)
    ticks = [_bid_ask(end - i, 100.0, 100.25) for i in range(1000)]
    result = service.on_ticks_bid_ask(42, ticks, done=False)
    assert result["followup"] is not None
    assert result["completed"] == []
    assert service.state(target) == "loading"


def test_ac_d36_2_short_final_page_finishes_the_bar():
    bars = [_bar(BASE + i * 300) for i in range(2)]
    service = FootprintService("ES")
    service.sync_bars(bars, "5 mins")
    target = BASE  # the only completed bar
    # BID_ASK phase: short page → phase done; TRADES phase: short page →
    # bar done.
    for req_id, kind in ((42, "BID_ASK"), (43, "TRADES")):
        spec = service.next_wave(max_requests=1)[0]
        assert spec.kind == kind
        service.note_issued(req_id, spec)
        end = _end_ts(spec.end_str)
        if kind == "BID_ASK":
            ticks = [_bid_ask(end - 1 - i, 100.0, 100.25) for i in range(50)]
            result = service.on_ticks_bid_ask(req_id, ticks, done=True)
        else:
            ticks = [_trade(end - 1 - i, 100.5, 4) for i in range(50)]
            result = service.on_ticks_last(req_id, ticks, done=True)
    assert result["completed"] == [target]
    assert service.state(target) == "ready"
    assert service.pending_count() == 0
    # Merged levels carry both phases: [bidVol, askVol, tradeVol, count].
    lv = service.levels(target)
    assert lv[100.0][0] == 500.0   # 50 ticks × sizeBid 10
    assert lv[100.5][2] == 200.0   # 50 trades × 4
    assert lv[100.5][3] == 50


# ── AC-D36.3: zero reqTickByTickData anywhere ──────────────────────────

class _RecordingClient:
    """Fake IBKR client that records every method it receives."""

    def __init__(self):
        self.calls: list[str] = []

    def __getattr__(self, name):
        def _rec(*a, **k):
            self.calls.append(name)
        return _rec


def test_ac_d36_3_no_tick_by_tick_requests():
    from ibkr.tick_history import TickHistoryManager
    from ibkr.contracts import Contract
    client = _RecordingClient()
    mgr = TickHistoryManager(client)
    c = Contract()
    c.symbol = "ES"
    c.secType = "FUT"
    mgr.req_historical_ticks(c, startDateTime="", endDateTime="20261013-16:00:00",
                             numberOfTicks=1000, whatToShow="TRADES",
                             useRTH=1)
    # A1: the histogram path was removed (reqHistogramData takes no date
    # parameter — per-bar attribution impossible). AC-D36.3 is about
    # tick-by-tick only.
    mgr.cancel_historical_ticks(1)
    assert not any("tickbytick" in call.lower() for call in client.calls), \
        f"tick-by-tick used: {client.calls}"
    assert "reqHistoricalTicks" in client.calls


def test_ac_d36_3_no_tick_by_tick_in_tick_history_source():
    import pathlib
    src = pathlib.Path(__file__).resolve().parent.parent / "ibkr" / "tick_history.py"
    text = src.read_text()
    assert "reqTickByTickData(" not in text  # no call site (the docstring
    assert "tickByTick" not in text          # names it only to disclaim it)


def test_ac_d36_3_production_tree_has_no_mock_endpoint():
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


# ── AC-D36.4: zero static-layer regens on a 100-tick burst ─────────────

def test_ac_d36_4_100_tick_burst_zero_static_regens(qapp):
    """D28 discipline: per-tick updates never regenerate static footprint."""
    from ui.chart_panel import ChartPanel
    panel = ChartPanel()
    bars = [_bar(BASE + i * 300) for i in range(10)]
    panel.update_chart(bars)
    panel._fp_enabled_ui = True
    panel._symbol = "ES"
    panel._candle_half_width = 0.25
    snapshot = {"style": "classic", "metric": "volume",
                "levels": {b.ts: {100.0: [10.0, 6.0, 0.0, 0]} for b in bars},
                "states": {b.ts: "ready" for b in bars},
                "no_tick_data": False,
                "proxy_label": "ES tape"}
    panel.refresh_footprint(snapshot)
    panel.footprint_static.regen_count = 0
    # 100 per-tick same-bar updates (is_new_candle=False).
    for _ in range(100):
        panel.update_last_bar(_bar(bars[-1].ts), is_new_candle=False)
    assert panel.footprint_static.regen_count == 0


# ── 36.2 wave mechanics: cap, newest-first, lazy-fill, loading ─────────

def test_wave_cap_60_requests():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(100)]
    service.sync_bars(bars, "5 mins")
    specs = service.next_wave(max_requests=60)
    assert len(specs) == 60


def test_wave_newest_first():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(10)]
    service.sync_bars(bars, "5 mins")
    specs = service.next_wave(max_requests=60)
    tss = [s.bar_ts for s in specs]
    assert tss == sorted(tss, reverse=True)


def test_lazy_fill_prioritises_visible_bars():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(20)]
    service.sync_bars(bars, "5 mins")
    # Visible = oldest 5 bars only.
    service.set_visible_range(BASE, BASE + 4 * 300)
    specs = service.next_wave(max_requests=5)
    assert len(specs) == 5
    assert all(s.bar_ts <= BASE + 4 * 300 for s in specs)


def test_loading_state_until_data_ready():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(3)]
    service.sync_bars(bars, "5 mins")
    assert service.state(BASE) == "loading"
    spec = service.next_wave(max_requests=1)[0]
    service.note_issued(7, spec)
    # Issued but no ticks yet → still loading.
    assert service.state(spec.bar_ts) == "loading"


def test_no_tick_data_after_consecutive_empty_first_pages():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(4)]
    service.sync_bars(bars, "5 mins")
    # Three consecutive empty BID_ASK first pages → unavailable.
    for i in range(3):
        spec = service.next_wave(max_requests=1)[0]
        assert spec.kind == "BID_ASK"
        service.note_issued(100 + i, spec)
        service.on_ticks_bid_ask(100 + i, [], done=False)
        if service.no_tick_data:
            break
        # Drain this bar's TRADES phase so the next wave hits the next
        # bar's BID_ASK first page.
        spec2 = service.next_wave(max_requests=1)[0]
        assert spec2.kind == "TRADES" and spec2.bar_ts == spec.bar_ts
        service.note_issued(200 + i, spec2)
        service.on_ticks_last(200 + i, [], done=True)
    assert service.no_tick_data
    assert service.state(BASE) == "unavailable"
    assert service.pending_count() == 0


def test_forming_refresh_yields_to_backfill():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(3)]
    service.sync_bars(bars, "5 mins")
    assert not service.forming_due(time.time()), \
        "forming refresh must yield while backfill pages are pending"


def test_forming_refresh_allowed_when_backfill_idle():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(2)]
    service.sync_bars(bars, "5 mins")
    # Complete both phases for the single completed bar.
    for req_id, cb in ((9, "bidask"), (10, "trades")):
        spec = service.next_wave(max_requests=1)[0]
        service.note_issued(req_id, spec)
        end = _end_ts(spec.end_str)
        if cb == "bidask":
            service.on_ticks_bid_ask(req_id, [_bid_ask(end, 100.0, 100.25)],
                                    done=True)
        else:
            service.on_ticks_last(req_id, [_trade(end, 100.5, 4)], done=True)
    assert service.pending_count() == 0
    assert service.forming_due(time.time())
    start_str, end_str = service.forming_window()
    assert _end_ts(start_str) == bars[-1].ts
    assert end_str == ""


def test_forming_ticks_replace_not_accumulate():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 300) for i in range(2)]
    service.sync_bars(bars, "5 mins")
    forming_ts = bars[-1].ts
    service.apply_forming_ticks([_bid_ask(forming_ts + 10, 100.0, 100.25,
                                          size_bid=5, size_ask=5)], "BID_ASK")
    service.apply_forming_ticks([_bid_ask(forming_ts + 20, 100.0, 100.25,
                                          size_bid=5, size_ask=5)], "BID_ASK")
    lv = service.levels(forming_ts)
    # Replace semantics: the second refresh overwrites the first.
    assert lv[100.0][0] == 5.0
    assert lv[100.25][1] == 5.0


# ── pacing arithmetic: 10-session burst ────────────────────────────────

def test_10_session_burst_fits_pacing_budget():
    from ibkr.pacing import pacing_manager
    # 10 sessions each planning a ≤60 wave = ≤600 requests total against
    # the rolling 600s historical budget.
    wave_total = 0
    for _ in range(10):
        service = FootprintService("ES")
        bars = [_bar(BASE + i * 300) for i in range(60)]
        service.sync_bars(bars, "5 mins")
        wave_total += len(service.next_wave(max_requests=60))
    assert wave_total <= 600
    assert pacing_manager.historical_wait_seconds() >= 0.0


# ── 36.3 index proxy + 36.4 cache keys ─────────────────────────────────

def test_spx_resolves_to_es_front_month_with_label():
    from ibkr.contracts import resolve_footprint_contract
    key, contract, label = resolve_footprint_contract("SPX")
    assert key.startswith("ES"), key
    assert contract.secType == "FUT"
    assert label == "ES tape"


def test_spy_uses_own_contract_no_proxy():
    from ibkr.contracts import resolve_footprint_contract
    key, contract, label = resolve_footprint_contract("SPY")
    assert key == "SPY"
    assert contract.secType == "STK"
    assert label == ""


def test_rollover_key_change_isolates_tape():
    from ibkr.contracts import footprint_cache_key
    from datetime import datetime
    from zoneinfo import ZoneInfo
    et = ZoneInfo("America/Toronto")
    key1 = footprint_cache_key("SPX", now=datetime(2026, 10, 13, tzinfo=et))
    key2 = footprint_cache_key("SPX", now=datetime(2027, 2, 1, tzinfo=et))
    assert key1.startswith("ES")
    assert key2.startswith("ES")
    assert key1 != key2  # front-month rollover → different key


def test_cache_round_trip_and_cacheable_only():
    from data.footprint_cache import FootprintCache, is_cacheable
    assert is_cacheable("SPX") and is_cacheable("SPY") and is_cacheable("QQQ")
    assert is_cacheable("ES") and is_cacheable("NQ")
    assert not is_cacheable("AAPL")
    con = sqlite3.connect(":memory:")
    con.execute(
        "CREATE TABLE footprint_cache (resolved_contract TEXT, date TEXT,"
        " timeframe TEXT, blob BLOB,"
        " PRIMARY KEY (resolved_contract, date, timeframe))")
    cache = FootprintCache(con)
    blob = {BASE: {100.0: [10.0, 6.0, 4.0, 1]}}
    cache.put("ESZ6", "2026-10-13", "5 mins", blob)
    got = cache.get("ESZ6", "2026-10-13", "5 mins")
    assert got == blob
    assert cache.get("ESZ6", "2026-10-14", "5 mins") is None
    # Rollover isolation: old front-month key never serves the new one.
    assert cache.get("ESH7", "2026-10-13", "5 mins") is None


# ── 36.5 rendering: style toggle × metric selector ─────────────────────

def _entries(tss):
    return [(float(i), {100.0: [10.0, 6.0, 16.0, 3],
                        100.25: [4.0, 9.0, 13.0, 2]})
            for i, ts in enumerate(tss)]


def test_footprint_item_classic_renders(qapp):
    item = FootprintItem()
    entries = _entries([1.0, 2.0, 3.0])
    item.set_data(entries, FootprintItem.STYLE_CLASSIC,
                  FootprintItem.METRIC_VOLUME, half_width=0.25)
    assert item.regen_count == 1
    item.set_data(entries, FootprintItem.STYLE_CLASSIC,
                  FootprintItem.METRIC_VOLUME, half_width=0.25)
    assert item.regen_count == 2


def test_footprint_item_heatmap_volume_and_count(qapp):
    item = FootprintItem()
    entries = _entries([1.0, 2.0])
    item.set_data(entries, FootprintItem.STYLE_HEATMAP,
                  FootprintItem.METRIC_VOLUME, half_width=0.25)
    assert item.regen_count == 1
    item.set_data(entries, FootprintItem.STYLE_HEATMAP,
                  FootprintItem.METRIC_COUNT, half_width=0.25)
    assert item.regen_count == 2  # metric change → re-render


def test_daily_timeframe_bars_backfill():
    service = FootprintService("ES")
    bars = [_bar(BASE + i * 86400, timeframe="1 day") for i in range(5)]
    service.sync_bars(bars, "1 day")
    specs = service.next_wave(max_requests=60)
    # 4 completed bars (last is forming-only).
    assert len(specs) == 4
    # A5: the forming bar is never a wave member, but it reads LOADING
    # pre-first-refresh (data is coming on the forming timer) — not
    # UNAVAILABLE (which would wrongly imply no data can ever arrive).
    assert service.state(bars[-1].ts) == "loading"


# ── session plumbing: wave cap + lazy viewport (fake client) ───────────

class _FakeTickClient(_RecordingClient):
    def reqHistoricalTicks(self, reqId, *a, **k):
        self.calls.append("reqHistoricalTicks")

    def cancelHistoricalTicks(self, reqId):
        self.calls.append("cancelHistoricalTicks")


class _StubStatusBar:
    def showMessage(self, msg, ms=0):
        pass


class _StubHost:
    def __init__(self, client):
        from ibkr.market_data import MarketDataManager
        from ibkr.tick_history import TickHistoryManager
        from data.footprint_cache import FootprintCache
        self.ib_client = client
        self.md_manager = MarketDataManager(client)
        self.tick_history_manager = TickHistoryManager(client)
        con = sqlite3.connect(":memory:")
        con.execute(
            "CREATE TABLE footprint_cache (resolved_contract TEXT, date TEXT,"
            " timeframe TEXT, blob BLOB,"
            " PRIMARY KEY (resolved_contract, date, timeframe))")
        self.footprint_cache = FootprintCache(con)
        self.status_bar = _StubStatusBar()
        self._req_table: dict[int, object] = {}

    def _register_req_id(self, req_id, session):
        self._req_table[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_table.pop(req_id, None)

    def _on_session_wave_complete(self, session):
        pass


def _make_session(qapp, symbol="SPX"):
    from ui.ticker_session import TickerSession
    client = _FakeTickClient()
    host = _StubHost(client)
    return client, host, TickerSession(symbol, host)


def test_session_wave_never_exceeds_60_requests(qapp):
    client, host, session = _make_session(qapp)
    bars = [_bar(BASE + i * 300) for i in range(100)]
    session._bars["5 mins"] = bars
    session.footprint_enable(timeframe="5 mins")
    tick_calls = [c for c in client.calls if c == "reqHistoricalTicks"]
    # 99 completed bars × 1 first-page spec, capped at 60 per wave.
    assert 0 < len(tick_calls) <= 60
    assert not any("tickbytick" in c.lower() for c in client.calls)


def test_session_viewport_sync_lazy_fills(qapp):
    client, host, session = _make_session(qapp)
    bars = [_bar(BASE + i * 300) for i in range(10)]
    session._bars["5 mins"] = bars
    session.footprint_enable(timeframe="5 mins")
    assert len(host._req_table) == 9  # enable-wave issued one page per bar
    # Simulate the wave's requests resolving without data so the bars are
    # plannable again, then scroll the viewport to the oldest 3 bars.
    for req_id in list(host._req_table):
        session._footprint.forget_request(req_id)
    session.sync_footprint_viewport(BASE, BASE + 2 * 300)
    specs = session._footprint.next_wave(max_requests=3)
    assert len(specs) == 3
    assert {s.bar_ts for s in specs} == {BASE, BASE + 300, BASE + 600}


def test_session_snapshot_carries_states_and_proxy_label(qapp):
    client, host, session = _make_session(qapp)
    bars = [_bar(BASE + i * 300) for i in range(3)]
    session._bars["5 mins"] = bars
    session.footprint_enable(timeframe="5 mins")
    snap = session.footprint_snapshot("5 mins")
    assert snap["proxy_label"] == "ES tape"
    assert snap["style"] == "classic"
    assert snap["metric"] == "volume"
    assert snap["no_tick_data"] is False
    assert set(snap["states"]) == {b.ts for b in bars}
    assert snap["states"][BASE] == "loading"
