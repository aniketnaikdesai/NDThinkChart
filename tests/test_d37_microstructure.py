"""test_d37_microstructure.py — D37 (depth heatmap + auction imbalance).

Acceptance criteria:
- AC-D37.1: synthetic insert/update/delete ops → heatmap level sizes match
  the book exactly.
- AC-D37.2: imbalance = (bidVol−askVol)/(bidVol+askVol) over top N,
  sign-correct (top-5 headline, top-10 toggle).
- AC-D37.3: synthetic 34/35/36 → the auction chip shows volume/price/
  imbalance; absent ticks → "no auction data".
- AC-D37.4: error 354 (no depth entitlement) → explicit panel state naming
  the issue (mocked client).
- AC-D37.5: full suite green (run separately), no D1–D36 regressions.

Plus: S0 generic-tick substrate (union subscription, reqId routing),
depth-feed budget + MD-line guard behaviour, D28 zero-regen discipline for
depth op bursts, price-aligned rows, and the no-mock-endpoint production
tree rule (owner-mandated, D36 pattern).
"""

import pytest

from services.depth_heatmap import (
    DepthHeatmapService, OP_INSERT, OP_UPDATE, OP_DELETE,
    SIDE_ASK, SIDE_BID, BUCKET_SECONDS,
)
from services.md_line_guard import assess


# ── Fakes (tests only — never production) ─────────────────────────────

class _FakeClient:
    """Records IBKR calls; never touches the wire."""
    def __init__(self):
        self.calls: list[tuple] = []
        self._next_id = 1000

    def _rid(self):
        self._next_id += 1
        return self._next_id

    def reqMktData(self, reqId, contract, genericTickList="",
                   snapshot=False, regulatorySnapshot=False,
                   mktDataOptions=None):
        self.calls.append(("reqMktData", reqId, genericTickList))

    def cancelMktData(self, reqId):
        self.calls.append(("cancelMktData", reqId))

    def reqMktDepth(self, reqId, contract, numRows,
                    isSmartDepth=False, mktDepthOptions=None):
        self.calls.append(("reqMktDepth", reqId, numRows, isSmartDepth))

    def cancelMktDepth(self, reqId, isSmartDepth=False):
        self.calls.append(("cancelMktDepth", reqId))


class _StubStatusBar:
    def __init__(self):
        self.messages: list[str] = []

    def showMessage(self, text, timeout=0):
        self.messages.append(text)


class _StubHost:
    def __init__(self, client, guard_md=True, guard_depth=True):
        from ibkr.market_data import MarketDataManager
        from ibkr.market_depth import MarketDepthManager
        from ibkr.subscription_manager import SubscriptionManager
        self.md_manager = MarketDataManager(client)
        self.depth_manager = MarketDepthManager(client)
        self.sub_manager = SubscriptionManager()
        self.status_bar = _StubStatusBar()
        self._req_table: dict[int, object] = {}
        self._guard_md = guard_md
        self._guard_depth = guard_depth

    def _register_req_id(self, req_id, session):
        self._req_table[req_id] = session

    def _unregister_req_id(self, req_id):
        self._req_table.pop(req_id, None)

    def _guard_md_lines(self, symbol, purpose):
        if not self._guard_md:
            self.status_bar.showMessage(
                f"Market-data line budget exceeded (100/100) — "
                f"not subscribing {purpose} for {symbol}.")
            return False
        return True

    def _guard_depth_budget(self, symbol):
        if not self._guard_depth:
            self.status_bar.showMessage(
                f"Depth feed budget exceeded (60) — no depth for {symbol}.")
            return False
        return True


def _make_session(qapp, symbol="SPX", **host_kw):
    from ui.ticker_session import TickerSession
    client = _FakeClient()
    host = _StubHost(client, **host_kw)
    return client, host, TickerSession(symbol, host)


class _FakeView:
    pass


# ── AC-D37.1: book bookkeeping ─────────────────────────────────────────

def test_ac_d37_1_insert_update_delete_match_book():
    svc = DepthHeatmapService("SPX")
    # Insert bid 100@10.0 and ask 200@10.5.
    svc.on_depth_op(0, OP_INSERT, SIDE_BID, 10.0, 100)
    svc.on_depth_op(0, OP_INSERT, SIDE_ASK, 10.5, 200)
    book = svc.book()
    assert book[10.0] == (100, 0)
    assert book[10.5] == (0, 200)
    # Update the bid size.
    svc.on_depth_op(0, OP_UPDATE, SIDE_BID, 10.0, 150)
    assert svc.book()[10.0] == (150, 0)
    # Delete the ask row.
    svc.on_depth_op(0, OP_DELETE, SIDE_ASK, 10.5, 0)
    assert 10.5 not in svc.book()
    # Matrix snapshots carry the resting sizes.
    svc.roll_bucket()
    matrix = svc.matrix()
    assert len(matrix) == 1
    assert matrix[0][10.0] == (150, 0)
    # Matrix is bounded.
    for _ in range(70):
        svc.roll_bucket()
    assert len(svc.matrix()) == 60


# ── AC-D37.2: imbalance ───────────────────────────────────────────────

def test_ac_d37_2_imbalance_formula_sign_correct():
    svc = DepthHeatmapService("SPX")
    # 5 bid levels of 100, 5 ask levels of 300.
    for i in range(5):
        svc.on_depth_op(i, OP_INSERT, SIDE_BID, 100.0 - i * 0.5, 100)
        svc.on_depth_op(i, OP_INSERT, SIDE_ASK, 100.5 + i * 0.5, 300)
    imb5 = svc.imbalance(5)
    assert imb5 == pytest.approx((500 - 1500) / 2000)  # -0.5
    assert imb5 < 0  # ask-heavy → negative
    # Top-10 sees only the 5 real levels each side → same ratio.
    assert svc.imbalance(10) == pytest.approx(imb5)
    # Flip the book: bids dominate → positive.
    svc2 = DepthHeatmapService("SPX")
    svc2.on_depth_op(0, OP_INSERT, SIDE_BID, 10.0, 900)
    svc2.on_depth_op(0, OP_INSERT, SIDE_ASK, 10.5, 100)
    assert svc2.imbalance(5) == pytest.approx(0.8)
    # Empty book → 0.0, never NaN.
    assert DepthHeatmapService("SPX").imbalance(5) == 0.0


def test_ac_d37_2_imbalance_top5_vs_top10():
    svc = DepthHeatmapService("SPX")
    # 10 bid levels: top-5 hold 100 each, levels 6-10 hold 1000 each.
    for i in range(10):
        size = 100 if i < 5 else 1000
        svc.on_depth_op(i, OP_INSERT, SIDE_BID, 100.0 - i * 0.5, size)
        svc.on_depth_op(i, OP_INSERT, SIDE_ASK, 100.5 + i * 0.5, 100)
    top5 = svc.imbalance(5)    # (500-500)/1000 = 0
    top10 = svc.imbalance(10)  # (5500-1000)/6500 > 0
    assert top5 == pytest.approx(0.0)
    assert top10 == pytest.approx(4500 / 6500)
    assert top10 > top5  # the toggle changes the headline


# ── AC-D37.3: auction chip ────────────────────────────────────────────

def test_ac_d37_3_auction_ticks_drive_chip(qapp):
    from ui.chart_panel import ChartPanel
    panel = ChartPanel()
    # Absent ticks → explicit "no data" state.
    panel.update_auction_chip(
        {"volume": None, "price": None, "imbalance": None,
         "reg_imbalance": None})
    assert panel._auction_chip.text() == "AUC —"
    # Synthetic 34/35/36 → chip shows volume/price/imbalance.
    panel.update_auction_chip(
        {"volume": 125000, "price": 6012.50, "imbalance": 40000,
         "reg_imbalance": 40000})
    text = panel._auction_chip.text()
    assert "BID" in text and "40,000" in text and "6012.50" in text
    # Ask-side imbalance flips the side label.
    panel.update_auction_chip(
        {"volume": 90000, "price": 6010.00, "imbalance": -25000,
         "reg_imbalance": -25000})
    assert "ASK" in panel._auction_chip.text()


def test_ac_d37_3_session_routes_auction_ticks(qapp):
    client, host, session = _make_session(qapp)
    session.attach_view(_FakeView(), "5 mins", sync=False)
    assert session.s0_req_id is not None
    # Generic "225" was requested on the session's S0 reqMktData.
    s0_calls = [c for c in client.calls if c[0] == "reqMktData"]
    assert len(s0_calls) == 1
    assert s0_calls[0][2] == "225"
    # Tick 34 (size) → volume; tick 35 (price) → price; 36 → imbalance.
    session.on_tick_size(session.s0_req_id, 34, 125000)
    session.on_tick_price(session.s0_req_id, 35, 6012.50)
    session.on_tick_size(session.s0_req_id, 36, 40000)
    state = session.auction_state()
    assert state["volume"] == 125000
    assert state["price"] == 6012.50
    assert state["imbalance"] == 40000
    # Wrong reqId is ignored (routing discipline).
    session.on_tick_size(999999, 34, 1)
    assert session.auction_state()["volume"] == 125000


# ── AC-D37.4: 354 degradation ─────────────────────────────────────────

def test_ac_d37_4_error_354_gives_explicit_state(qapp):
    client, host, session = _make_session(qapp)
    states: list[str] = []
    session.depth_state_changed.connect(states.append)
    req_id = session.ensure_depth_subscribed()
    assert req_id is not None
    assert session.depth_state == "live"
    # Server-side 354: no depth entitlement.
    session.on_depth_error(354, "Not subscribed to requested market data")
    assert session.depth_state == "no_entitlement"
    assert states[-1] == "no_entitlement"
    # The feed is released — no dangling subscription.
    assert session.depth_req_id is None
    cancels = [c for c in client.calls if c[0] == "cancelMktDepth"]
    assert cancels, "expected cancelMktDepth on 354"


def test_ac_d37_4_panel_names_the_issue(qapp):
    from ui.chart_panel import ChartPanel
    panel = ChartPanel()
    panel.set_depth_state("no_entitlement")
    assert panel._depth_state_text.toPlainText() == \
        "Depth subscription required"
    assert panel._depth_state_text.isVisible()
    panel.set_depth_state("live")
    assert not panel._depth_state_text.isVisible()


# ── S0 substrate: union + lifecycle ───────────────────────────────────

def test_s0_union_merges_feature_needs(qapp):
    client, host, session = _make_session(qapp)
    session.attach_view(_FakeView(), "5 mins", sync=False)  # registers auction {"225"}
    session.s0_register("news", {"292", "456"})
    calls = [c for c in client.calls if c[0] == "reqMktData"]
    assert len(calls) == 2  # re-subscribed once: union changed
    assert calls[-1][2] == "225,292,456"
    # Unchanged union → no re-subscribe.
    session.s0_register("news", {"456", "292"})
    assert len([c for c in client.calls if c[0] == "reqMktData"]) == 2
    # Last feature deregisters → cancel, no standalone reqMktData.
    session.s0_deregister("news")
    session.s0_deregister("auction")
    assert session.s0_req_id is None
    cancels = [c for c in client.calls if c[0] == "cancelMktData"]
    assert len(cancels) == 3  # one per union change + final cancel


def test_s0_detach_last_view_cancels(qapp):
    client, host, session = _make_session(qapp)
    view = _FakeView()
    session.attach_view(view, "5 mins", sync=False)
    assert session.s0_req_id is not None
    # Monitored sessions survive detach (headless alarms) but drop S0.
    session.monitored = True
    session.detach_view(view)
    assert session.s0_req_id is None
    assert session.view_count == 0


def test_s0_md_guard_refusal_is_explicit(qapp):
    client, host, session = _make_session(qapp, guard_md=False)
    session.attach_view(_FakeView(), "5 mins", sync=False)
    # Guard refused → no reqMktData, union cleared, warning names the symbol.
    assert session.s0_req_id is None
    assert not any(c[0] == "reqMktData" for c in client.calls)
    assert any("SPX" in m for m in host.status_bar.messages)


# ── Depth feed: budget, refcount, MD guard ────────────────────────────

def test_depth_feed_refcounted_per_session(qapp):
    client, host, session = _make_session(qapp)
    r1 = session.ensure_depth_subscribed()
    r2 = session.ensure_depth_subscribed()
    assert r1 == r2  # one reqMktDepth per session
    assert len([c for c in client.calls if c[0] == "reqMktDepth"]) == 1
    session.release_depth()
    assert session.depth_req_id is not None  # still held
    session.release_depth()
    assert session.depth_req_id is None
    assert any(c[0] == "cancelMktDepth" for c in client.calls)


def test_depth_budget_refusal_is_explicit(qapp):
    client, host, session = _make_session(qapp, guard_depth=False)
    assert session.ensure_depth_subscribed() is None
    assert session.depth_state == "budget_exceeded"
    assert not any(c[0] == "reqMktDepth" for c in client.calls)


def test_depth_md_guard_refusal_is_explicit(qapp):
    client, host, session = _make_session(qapp, guard_md=False)
    assert session.ensure_depth_subscribed() is None
    assert session.depth_state == "budget_exceeded"


def test_depth_manager_shared_feeds_refcount():
    from ibkr.market_depth import MarketDepthManager
    client = _FakeClient()
    mgr = MarketDepthManager(client)
    r1 = mgr.subscribe_shared("SPX", object())
    r2 = mgr.subscribe_shared("SPX", object())
    assert r1 == r2
    assert len([c for c in client.calls if c[0] == "reqMktDepth"]) == 1
    mgr.release_shared("SPX")
    assert mgr.shared_req_id("SPX") == r1  # still held
    mgr.release_shared("SPX")
    assert mgr.shared_req_id("SPX") is None
    assert any(c[0] == "cancelMktDepth" for c in client.calls)


# ── MD-line guard (37.5) ──────────────────────────────────────────────

def test_md_line_guard_thresholds():
    level, msg = assess(50, "SPX", "depth")
    assert level == "ok" and msg == ""
    level, msg = assess(90, "SPX", "depth")
    assert level == "approaching"
    assert "SPX" in msg and "90/100" in msg
    level, msg = assess(100, "SPX", "S0 ticks")
    assert level == "exceeded"
    assert "SPX" in msg and "not subscribing" in msg


# ── D28 discipline: no regen on op bursts; price alignment ────────────

def test_depth_op_burst_causes_zero_regens(qapp):
    from ui.depth_heatmap_item import DepthHeatmapItem
    item = DepthHeatmapItem()
    svc = DepthHeatmapService("SPX")
    for i in range(100):
        svc.on_depth_op(i, OP_INSERT, SIDE_BID, 100.0 - i * 0.01, 50 + i)
    svc.roll_bucket()
    item.set_matrix(svc.matrix(), 0.005)
    assert item.regen_count == 0  # data-only path never regenerates
    item.refresh()
    assert item.regen_count == 1


def test_heatmap_rows_are_price_aligned(qapp):
    from ui.depth_heatmap_item import DepthHeatmapItem
    item = DepthHeatmapItem()
    buckets = [{100.0: (50, 0), 100.5: (0, 70)}]
    cells = item.layout(view_right=1000.0, view_width=500.0)
    # Empty before data is set.
    assert cells == []
    item.set_matrix(buckets, 0.25)
    cells = item.layout(view_right=1000.0, view_width=500.0)
    by_price = {p: (x0, cw, sizes) for x0, cw, p, sizes in cells}
    assert set(by_price) == {100.0, 100.5}
    # Columns are time-ordered left→right ending at the visible right edge.
    assert by_price[100.0][0] < 1000.0


# ── Bridge signals (37.0) ─────────────────────────────────────────────

def test_bridge_tick_generic_string_news_signals(qapp):
    from ibkr.bridge import IBBridge
    b = IBBridge()
    seen: list[tuple] = []
    b.tick_generic.connect(lambda r, t, v: seen.append(("g", r, t, v)))
    b.tick_string.connect(lambda r, t, v: seen.append(("s", r, t, v)))
    b.tick_news.connect(
        lambda r, ts, pc, aid, h: seen.append(("n", r, ts, pc, aid, h)))
    b.tick_generic.emit(7, 46, 1.25)
    b.tick_string.emit(7, 59, "0.42")
    b.tick_news.emit(7, 1700000000, "BRFG", "BRFG$abc", "Headline")
    assert seen[0] == ("g", 7, 46, 1.25)
    assert seen[1] == ("s", 7, 59, "0.42")
    assert seen[2][0] == "n" and seen[2][5] == "Headline"


def test_client_overrides_match_10_51_1_signatures():
    import inspect
    from ibkr.client import IBApiClient
    assert list(inspect.signature(IBApiClient.tickGeneric).parameters) == \
        ["self", "reqId", "tickType", "value"]
    assert list(inspect.signature(IBApiClient.tickString).parameters) == \
        ["self", "reqId", "tickType", "value"]
    assert list(inspect.signature(IBApiClient.tickNews).parameters) == \
        ["self", "tickerId", "timeStamp", "providerCode",
         "articleId", "headline", "extraData"]


# ── Owner rule: no mock endpoint in production code ───────────────────

def test_ac_d37_production_tree_has_no_mock_endpoint():
    """Owner rule (D36 pattern): fakes live in tests/ only."""
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
