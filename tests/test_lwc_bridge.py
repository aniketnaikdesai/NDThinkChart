"""tests/test_lwc_bridge.py — P6-T04 Phase 2 runtime + self-healing bridge.

Offline ``QWebEngineView`` host (vendored v5.2.x via ``ndt://``, deny-default
interceptor, attribution) and the batched ``QWebChannel`` ``LwBridge``
(``{v:1,ops:[]}`` column-array ops, queue-until-ready, ~33 ms live coalesce,
full op-log replay after ``renderProcessTerminated``).

Webengine-gated cases (DG88/A110/AP-P6-4) carry ``@pytest.mark.webengine``
and skip — never red — where Chromium is unavailable; every skip names its
manual-checklist counterpart.
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ui import lwc_bridge as LB
from ui import lwc_host as LH

REPO = Path(__file__).resolve().parent.parent
LWC_DIR = REPO / "chart_assets" / "lwc"

MANUAL_HOST = (
    "manual: P6-04 checklist §offline-host on a Chromium box "
    "(DG88 webengine viability probe)"
)
MANUAL_INTERCEPTOR = (
    "manual: P6-04 checklist §deny-default on a Chromium box "
    "(https/http blocked, ndt allowed)"
)
MANUAL_RECOVERY = (
    "manual: P6-04 checklist §renderer-recovery on a Chromium box "
    "(kill renderer, series re-renders with no dup/loss)"
)

GATED = [
    "test_interceptor_wired_blocks_non_ndt",
    "test_host_loads_ndt_chart_offline",
    "test_render_terminated_recovery_wired",
]


def _bars(ts0=1_700_000_000, n=5, step=60):
    return [
        SimpleNamespace(
            ts=ts0 + i * step,
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.5 + i,
            volume=1000 + i,
        )
        for i in range(n)
    ]


# ── T11 · offline / interceptor (AC1) ─────────────────────────────────────


class TestOfflineInterceptor:
    def test_version_pin_asserted(self):
        pinned = LH.LWC_PINNED_VERSION
        declared = (LWC_DIR / "VERSION").read_text(encoding="utf-8").strip()
        assert pinned == declared, "host pin must equal the VERSION file"
        assert pinned == "5.2.1", "this wave pins the v5.2.x tree at 5.2.1"
        header = (LWC_DIR / "lightweight-charts.standalone.production.js").read_text(
            encoding="utf-8"
        )[:600]
        assert f"v{pinned}" in header, "vendored header must declare the pin"

    def test_ndt_registered_before_qapp_ordering_probe(self):
        """Fresh interpreter: register before any QApplication → True."""
        code = (
            "import sys; sys.path.insert(0, %r);"
            "from ui.lwc_host import register_ndt_scheme;"
            "sys.stdout.write(str(register_ndt_scheme()))" % str(REPO)
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            timeout=120,
        )
        assert proc.returncode == 0, proc.stderr[-2000:]
        assert proc.stdout.strip() == "True", (
            "ndt:// must register before QApplication "
            f"(got {proc.stdout.strip()!r})"
        )

    def test_interceptor_ndt_allowed_rest_blocked(self):
        assert LH.is_request_allowed("ndt://lwc/chart.html")
        assert LH.is_request_allowed("ndt://lwc/envelope.js")
        assert LH.is_request_allowed("qrc:///qtwebchannel/qwebchannel.js")
        for blocked in (
            "https://unpkg.com/lightweight-charts",
            "http://localhost:8000/chart.html",
            "http://127.0.0.1/x.js",
            "file:///etc/passwd",
            "ftp://example.com/x",
            "not a url at all !!!",
        ):
            assert not LH.is_request_allowed(blocked), blocked

    def test_attribution_present(self):
        assert (LWC_DIR / "ATTRIBUTION.md").is_file()
        text = LH.attribution_text()
        assert LH.LWC_PINNED_VERSION in text
        assert "Apache" in text

    def test_airplane_run_no_network_surface(self):
        """Our loader files reference no remote URL; our modules import no
        network stack — the suite passes with no network (airplane)."""
        for name in ("chart.html", "chart.js", "envelope.js"):
            src = (LWC_DIR / name).read_text(encoding="utf-8")
            assert "https://" not in src and "http://" not in src, name
            assert "unpkg" not in src and "cdn" not in src.lower(), name
        for mod in ("ui/lwc_host.py", "ui/lwc_bridge.py"):
            src = (REPO / mod).read_text(encoding="utf-8")
            assert "import socket" not in src, mod
            assert "urllib.request" not in src, mod
            assert "import requests" not in src, mod

    def test_focus_keyboard_model_named(self):
        assert LH.FOCUS_KEYBOARD_MODEL.startswith("lwc-focus-forward-v1")


# ── T12 · batch shape (AC1) ───────────────────────────────────────────────


class TestBatchShape:
    def test_envelope_is_exactly_v1_ops(self):
        b = LB.LwBridge()
        b.set_ready(True)
        holder = {}

        def _capture(e):
            holder["env"] = e

        b.opsEmitted.connect(_capture)
        b.send_ops([LB.candles_set_op(_bars())])
        env = b.flush()
        assert env is not None
        assert set(env.keys()) == {"v", "ops"}
        assert env["v"] == 1 == LB.ENVELOPE_VERSION
        assert isinstance(env["ops"], list)
        cols = env["ops"][0]["cols"]
        assert set(cols) == {"ts", "open", "high", "low", "close"}
        assert all(isinstance(v, list) for v in cols.values())

    def test_queue_until_ready_holds_pre_ready_ops(self):
        b = LB.LwBridge()
        seen = []
        b.opsEmitted.connect(seen.append)
        bars = _bars()
        b.send_ops([LB.candles_set_op(bars), LB.volume_set_op(bars)])
        assert seen == [], "nothing may cross before ready"
        assert b.counters()["queued"] == 2
        assert b.counters()["queue_depth_max"] == 2
        b.set_ready(True)
        env = b.flush()
        assert env is not None and len(env["ops"]) == 2
        assert b.counters()["received"] == 2

    def test_live_coalesce_bounds_tick_crossing(self):
        b = LB.LwBridge()
        b.set_ready(True)
        seen = []
        b.opsEmitted.connect(seen.append)
        bar = _bars(n=1)[0]
        ticks = 300
        for i in range(ticks):
            bar = SimpleNamespace(
                ts=bar.ts, open=bar.open, high=bar.high + 0.01,
                low=bar.low, close=bar.close + 0.01, volume=bar.volume,
            )
            b.send_ops([LB.candle_update_op(bar)])
        assert LB.COALESCE_MS == 33, "~33 ms live window is the contract"
        assert b.counters()["coalesced"] == ticks - 1
        env = b.flush()
        assert env is not None and len(env["ops"]) == 1
        assert env["ops"][0]["cols"]["ts"] == [bar.ts]
        assert seen and len(seen) == 1, "one crossing for the whole burst"

    def test_distinct_forming_bars_do_not_merge(self):
        b = LB.LwBridge()
        b.set_ready(True)
        b.send_ops([LB.candle_update_op(x) for x in _bars(n=3)])
        env = b.flush()
        assert env is not None and len(env["ops"]) == 3


# ── T13 · replay identity (AC2) ───────────────────────────────────────────


class TestReplayIdentity:
    def _drive_session(self, b):
        bars = _bars()
        b.set_ready(True)
        b.send_ops([LB.candles_set_op(bars), LB.volume_set_op(bars)])
        assert b.flush() is not None
        live = SimpleNamespace(ts=bars[-1].ts + 60, open=1, high=2,
                               low=0.5, close=1.5, volume=7)
        for i in range(5):  # live storm on one forming bar
            live = SimpleNamespace(ts=live.ts, open=1, high=2 + i * 0.1,
                                   low=0.5, close=1.5 + i * 0.1, volume=7)
            b.send_ops([LB.candle_update_op(live)])
        assert b.flush() is not None
        return bars, live

    def test_replay_identity_no_dup_no_loss(self):
        b = LB.LwBridge()
        emitted = []
        b.opsEmitted.connect(emitted.append)
        bars, live = self._drive_session(b)
        expected = [(x.ts, x.open, x.high, x.low, x.close) for x in bars]
        expected.append((live.ts, live.open, live.high, live.low, live.close))

        b.handle_render_terminated()  # simulate renderProcessTerminated
        assert not b.is_ready
        replay_env = b.handle_page_ready()
        assert replay_env is not None
        assert replay_env["v"] == 1
        assert b.counters()["replays"] == 1

        rows = LB.apply_ops_to_bars(replay_env["ops"])
        assert rows == expected, "no duplicated or lost bars after replay"
        ts = [r[0] for r in rows]
        assert ts == sorted(set(ts))

    def test_replay_is_idempotent(self):
        b = LB.LwBridge()
        bars, live = self._drive_session(b)
        b.handle_render_terminated()
        first = b.handle_page_ready()
        second = b.handle_page_ready()
        assert LB.apply_ops_to_bars(first["ops"]) == LB.apply_ops_to_bars(
            second["ops"]
        )
        assert len(LB.apply_ops_to_bars(second["ops"])) == len(bars) + 1

    def test_replay_log_returns_full_history(self):
        b = LB.LwBridge()
        b.set_ready(True)
        b.send_ops([LB.candles_set_op(_bars(n=2))])
        b.flush()
        log = b.replay_log()
        assert len(log) == 1 and log[0]["op"] == "set_bars"
        log.clear()
        assert len(b.replay_log()) == 1, "replay_log returns a copy"


# ── T14 · marker audit (AC3) ──────────────────────────────────────────────


class TestMarkerAudit:
    def test_webengine_marker_registered(self):
        text = (REPO / "pytest.ini").read_text(encoding="utf-8")
        assert "webengine" in text, "pytest.ini must register the marker"

    def test_gated_cases_carry_the_mark(self):
        for name in GATED:
            fn = globals()[name]
            marks = [m.name for m in getattr(fn, "pytestmark", [])]
            assert "webengine" in marks, f"{name} must be @pytest.mark.webengine"

    def test_backpressure_counters_present_from_day_one(self):
        c = LB.LwBridge().counters()
        for key in ("received", "queued", "coalesced", "emitted",
                    "emissions", "replays", "queue_depth_max"):
            assert key in c, key


@pytest.mark.webengine
@pytest.mark.skipif(
    not LH.HAS_WEBENGINE,
    reason="no QtWebEngine here — " + MANUAL_INTERCEPTOR,
)
def test_interceptor_wired_blocks_non_ndt():
    from PyQt6.QtCore import QUrl

    seen = []

    class _Info:
        def __init__(self, url):
            self._url = QUrl(url)

        def requestUrl(self):
            return self._url

        def block(self, on):
            seen.append((self._url.toString(), bool(on)))

    ic = LH.LwcRequestInterceptor()
    chart_url = "ndt://lwc/chart.html"
    non_ndt = [
        "https://example.com/x.js",
        "http://127.0.0.1/x.js",
        "file:///etc/passwd",
    ]
    for url in [chart_url, *non_ndt]:
        ic.interceptRequest(_Info(url))

    # The real engine dispatches from its own IO thread, so arrival order is not
    # part of the contract — the per-URL verdict is. The interceptor implements
    # deny-default by calling ``block(True)`` only (Qt's default is allow), so
    # an allowed URL may carry no verdict at all.
    verdicts = dict(seen)
    assert len(verdicts) == len(seen), f"a request was intercepted twice: {seen}"

    assert verdicts.get(chart_url, False) is False, (
        f"the offline ndt:// chart URL must be allowed (seen: {seen})"
    )
    allowed = {url for url, blocked in verdicts.items() if not blocked}
    assert allowed <= {chart_url}, (
        "deny-default violated — non-ndt URLs were allowed: "
        f"{sorted(allowed - {chart_url})} (seen: {seen})"
    )
    not_blocked = sorted(set(non_ndt) - {url for url, on in verdicts.items() if on})
    assert not_blocked == [], (
        f"every non-ndt URL must be blocked, these were not: {not_blocked} "
        f"(seen: {seen})"
    )


@pytest.mark.webengine
@pytest.mark.skipif(
    not LH.HAS_WEBENGINE,
    reason="no QtWebEngine here — " + MANUAL_HOST,
)
def test_host_loads_ndt_chart_offline():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    bridge = LB.LwBridge()
    host = LH.LwcHost(bridge)
    assert host.host_url() == "ndt://lwc/chart.html"
    assert LH.FOCUS_KEYBOARD_MODEL.startswith("lwc-focus-forward-v1")


@pytest.mark.webengine
@pytest.mark.skipif(
    not LH.HAS_WEBENGINE,
    reason="no QtWebEngine here — " + MANUAL_RECOVERY,
)
def test_render_terminated_recovery_wired():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    bridge = LB.LwBridge()
    host = LH.LwcHost(bridge)
    assert hasattr(host, "_on_render_terminated")
    assert hasattr(bridge, "handle_render_terminated")
    assert hasattr(bridge, "handle_page_ready")


# ── T15 · residue scan (AC4, renderer-only boundary) ───────────────────────


class TestRendererBoundary:
    SOURCES = ["ui/lwc_host.py", "ui/lwc_bridge.py"]

    FORBIDDEN = [
        "from ibkr", "import ibkr", "ibkr.",
        "sqlite", "QSettings",
        "placeOrder", "cancelOrder", "OrderRate", "UserOrder",
        "watchlist", "dock", "pyqtgraph",
        "stop_loss", "take_profit",
        "unpkg", "jsdelivr", "cdnjs", "cdn.",
        "http://", "https://",
    ]

    def test_no_out_of_scope_surface(self):
        hits = []
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            for token in self.FORBIDDEN:
                if token in src:
                    hits.append(f"{rel}: {token!r}")
        assert hits == [], f"out-of-scope residue: {hits}"

    def test_no_db_store_or_service_wiring(self):
        for rel in self.SOURCES:
            src = (REPO / rel).read_text(encoding="utf-8")
            assert "get_bars" not in src and "save_bars" not in src, rel
            assert "BarCache" not in src and "session_service" not in src, rel
