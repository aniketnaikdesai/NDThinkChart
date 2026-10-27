"""tests/test_lwc_e2e_data.py — Q-19: data crosses the **real** transport.

Blank/empty-chart regression, **the data cause** (found by reading the real
page after a load, not by a unit test). Five independent defects each block the
bars from reaching the page:

* **S3a layout** — ``ui/lwc_view.py::ensure_host`` built the host with
  ``parent=self`` but never added it to a layout, so the host stayed at its
  default 100x30 inside the view;
* **S3b subscription** — ``chart_assets/lwc/chart.js::bindChannel`` only
  assigned ``window.lwBridge``; nothing subscribed to a bridge signal, so
  ``applyOps`` was reachable only from tests through ``window.lwApplyOps``;
* **S3c payload** — ``LwBridge.opsEmitted(dict)`` reaches JS as a Python repr
  string (``{'v': 1, ...}``), which is not JSON; the page rejects it;
* **S3d readiness race** — ``_on_load_finished`` replayed the op log before the
  page's QWebChannel subscription existed, so the replay had no listener;
* **S3e page→Python** — no ``pyqtSlot`` existed on the bridge, so the page's
  ``focusReleased()`` call was silently dropped.

Every earlier LWC data test bypassed the transport: they injected envelopes
through ``window.lwApplyOps`` or captured ``opsEmitted`` in Python. This module
never does either. It drives the real widget, the real page and the real
``update_chart`` path, then reads the page's own snapshot through
``runJavaScript``:

    window.lwSnapshot().candles.length == the plotted bar count

It **fails on the pre-Q-19 tree** (the snapshot stays empty: the page never
subscribed and the replay raced the handshake), and it is the gate evidence
that re-proves parity-matrix rows 1 (history render, all five modes) and 2
(live forming-bar tick, no history rebuild) through the transport.

``@pytest.mark.webengine`` per DG88/AP-P6-4. This is a JavaScript-answer test,
not a pixel test, so it runs under ``QT_QPA_PLATFORM=offscreen`` (the Q-15
display limitation applies only to rasterisation). The single pixel case —
Q-23's captured-bitmap check — is the exception and is gated by
``needs_rasteriser``.

**Q-20 — content, not counts.** The count-only cases above passed while the
time axis read ``01/01 01:29``: the wire carried logical indices and the page
rendered them as epoch seconds (1970). The cases below therefore assert the
page's *content*: the first/last series time equal the first/last bar ``ts``,
the axis' own visible range is that real time, a rendered tick label names the
bar's real date, and a drawing/alarm/key message raised **in the page** reaches
the Python signal. A counting test is not proof of the axis.
"""

from __future__ import annotations

import json
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from data.models import Bar  # noqa: E402
from ui import lwc_host as LH  # noqa: E402
from ui import lwc_view as LV  # noqa: E402

# The ``ndt://`` scheme is honoured only when registered before a
# ``QApplication`` exists (Q-13). Module import happens before any test body or
# conftest fixture constructs one, so this is the earliest safe point.
LH.register_ndt_scheme()

#: The proof needs no display; on an engine-less box the cases skip with this
#: manual counterpart.
MANUAL_E2E = (
    "manual: open the app on a Chromium box, load a symbol, and confirm the "
    "chart shows the bars (Q-19 checklist: history + live tick through the "
    "real QWebChannel transport)"
)


def _ensure_app():
    """The session ``QApplication`` with a real ``argv[0]``.

    Chromium aborts the interpreter ("the program name is not passed to
    QCoreApplication") when the application was built from an empty argv — a
    bare ``QApplication([])``. Creating it here, at import time, makes this
    module's app win over the conftest ``qapp`` fixture's empty-argv one.
    """
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest"])
    return app


try:  # an engine-less box must still import this module (skip, never red)
    APP = _ensure_app() if LH.HAS_WEBENGINE else None
except Exception:  # pragma: no cover — QApplication could not be built
    APP = None

needs_webengine = pytest.mark.skipif(
    not LH.HAS_WEBENGINE or APP is None,
    reason="no QtWebEngine here — " + MANUAL_E2E,
)


def _pump(app, ms: int) -> None:
    """Run the Qt event loop for ``ms`` milliseconds (no blocking exec_)."""
    from PyQt6.QtCore import QEventLoop

    deadline = time.monotonic() + ms / 1000.0
    while time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


def _wait_until(app, predicate, timeout_ms: int, what: str) -> None:
    from PyQt6.QtCore import QEventLoop

    deadline = time.monotonic() + timeout_ms / 1000.0
    last_error = None
    while time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        try:
            if predicate():
                return
        except RuntimeError as exc:  # page/page deleted between polls
            last_error = exc
        time.sleep(0.01)
    raise AssertionError(
        f"timed out after {timeout_ms} ms waiting for {what}"
        + (f" (last error: {last_error})" if last_error else "")
    )


def _run_js(host, js: str, timeout_ms: int = 5000):
    """Run ``js`` in the loaded page and return its JSON-decoded result."""
    from PyQt6.QtCore import QEventLoop, QTimer

    box = {}
    loop = QEventLoop()

    def done(result):
        box["result"] = result
        loop.quit()

    # Watchdog: a page that died never calls back; fail instead of wedging.
    QTimer.singleShot(timeout_ms, loop.quit)
    host.page().runJavaScript(js, 0, done)
    loop.exec()
    assert "result" in box, (
        f"runJavaScript never called back within {timeout_ms} ms — the page "
        "is not answering (renderer gone?)"
    )
    return box["result"]


def _candles(host):
    """The page's own candle snapshot (``window.lwSnapshot().candles``)."""
    rows = _run_js(host, "window.lwSnapshot().candles")
    return rows if isinstance(rows, list) else []


def _axis(host) -> dict:
    """The page's own time-axis probe (``window.lwAxisProbe()``, Q-20)."""
    probe = _run_js(host, "window.lwAxisProbe()")
    return probe if isinstance(probe, dict) else {}


def _layout_page(view) -> None:
    """Lay the view (and its page) out at its real size without a display.

    A hidden ``QWidget`` never runs its layout: the host stayed at Qt's
    default 100x30 and the page's viewport was 0x0, so the time scale's
    ``getVisibleRange()`` was ``null`` and its tick formatter never ran.
    ``WA_DontShowOnScreen`` runs the widget and page layout at the view's
    real size without opening a window — the offscreen answer to Q-15
    (layout is real; rasterisation is not needed).
    """
    from PyQt6.QtCore import Qt

    view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    view.show()


def _call_slot(host, slot: str, payload: dict):
    """Call a bridge slot from the page with one JSON string (Q-20).

    The page's own modules hand the slots a JSON string (the mirror of
    ``opsJson``), so the test raises exactly the message the page raises.
    """
    literal = json.dumps(json.dumps(payload))
    return _run_js(host, f"window.lwBridge.{slot}({literal})")


def _drain(app, rounds: int = 3) -> None:
    """Run the loop and flush deferred deletes — ``deleteLater`` needs this."""
    from PyQt6.QtCore import QCoreApplication, QEvent, QEventLoop

    for _ in range(rounds):
        try:
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
            QCoreApplication.sendPostedEvents(
                None, int(QEvent.Type.DeferredDelete)
            )
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        except Exception:  # pragma: no cover — teardown must never raise
            return


def _release_profile() -> None:
    """Uninstall this host's handlers from the application-owned profile.

    ``create_host`` installs the ``ndt://`` handler and the interceptor on
    ``QWebEngineProfile.defaultProfile()``. The profile outlives the view, so
    leaving them pointing at a deleted widget turns process exit into
    "Release of profile requested but WebEnginePage still not deleted" (Q-15).
    """
    from PyQt6.QtWebEngineCore import QWebEngineProfile

    try:
        profile = QWebEngineProfile.defaultProfile()
    except Exception:  # pragma: no cover — engine already gone
        return
    if profile is None:  # pragma: no cover
        return
    try:
        handler = profile.urlSchemeHandler(LH.NDT_SCHEME.encode())
    except Exception:  # pragma: no cover
        handler = None
    if isinstance(handler, LH.NdtSchemeHandler):
        try:
            profile.removeUrlSchemeHandler(handler)
        except Exception:  # pragma: no cover
            pass
    try:
        profile.setUrlRequestInterceptor(None)
    except Exception:  # pragma: no cover
        pass


def _teardown_view(app, view) -> None:
    """Deterministically dismantle the real host (Q-15/Q-16)."""
    if view is None:
        return

    host = getattr(view, "_host", None)
    try:
        bridge = view.bridge
    except Exception:  # pragma: no cover — C++ side already gone
        bridge = None

    page = None
    if host is not None:
        for call in (getattr(host, "stop", None), getattr(host, "hide", None)):
            if call is not None:
                try:
                    call()
                except Exception:  # pragma: no cover
                    pass
        try:
            page = host.page()
        except Exception:  # pragma: no cover
            page = None
    try:
        view.hide()
    except Exception:  # pragma: no cover
        pass

    if bridge is not None:
        for name in ("opsEmitted", "opsJson", "replayFinished",
                     "pageFocusReleased", "pageDrawingCommitted",
                     "pageDrawingUpdated", "pageDrawingDeleted",
                     "pageSelectionChanged", "pageAlarmCreated",
                     "pageAlarmMoved", "pageAlarmDeleted", "pageZoomRefused",
                     "pageKeyPressed"):
            signal = getattr(bridge, name, None)
            if signal is None:
                continue
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):  # nothing connected / gone
                pass

    if host is not None:
        _release_profile()

    try:
        view.deleteLater()
    except Exception:  # pragma: no cover
        pass
    if page is not None:
        try:
            page.deleteLater()
        except Exception:  # pragma: no cover
            pass
    if host is not None:
        try:
            host.deleteLater()
        except Exception:  # pragma: no cover
            pass

    _drain(app)


def _bars(n: int = 240, ts0: int = 1_700_000_000, step: int = 60) -> list:
    """A deterministic OHLCV series with rising closes and no gaps."""
    rows = []
    for i in range(n):
        base = 100.0 + (i % 20) * 0.5
        close = base + (0.4 if i % 2 == 0 else -0.3)
        rows.append(Bar(
            "TEST", "5 mins", ts0 + i * step, base,
            max(base, close) + 0.25, min(base, close) - 0.25, close,
            1000.0 + i,
        ))
    return rows


def _rth_bars_with_hole(n: int = 12, hole=(4, 5)) -> list:
    """5-minute RTH bars with a two-bar midday hole (Q-20 whitespace case).

    Monday 2026-09-28 13:30 UTC (09:30 ET, EDT) onward: the missing slots are
    inside the session, so they are a *hole*, not a collapsed non-trading gap.
    """
    from datetime import datetime, timezone

    base = int(datetime(2026, 9, 28, 13, 30, tzinfo=timezone.utc).timestamp())
    rows = []
    for i in range(n):
        if i in hole:
            continue
        price = 100.0 + i * 0.1
        rows.append(Bar("TEST", "5 mins", base + i * 300, price,
                        price + 0.25, price - 0.25, price + 0.05,
                        1000.0 + i))
    return rows


def _two_session_bars(n: int = 40) -> list:
    """The measured Q-22 fixture: 40 Fri + 40 Mon RTH bars, each from the open.

    Friday 2026-10-23 and Monday 2026-10-26 both start at 13:30 UTC (09:30 ET,
    EDT). The 5-minute blocks are separated by a whole weekend: 68.75 h of
    wall time, i.e. 824 periods. Before the fix this crossed as 904 ``ts``
    slots (824 placeholders), pinning the 80 candles to the two edges.
    """
    from datetime import datetime, timezone

    fri = int(datetime(2026, 10, 23, 13, 30, tzinfo=timezone.utc).timestamp())
    mon = int(datetime(2026, 10, 26, 13, 30, tzinfo=timezone.utc).timestamp())
    rows = []
    for base in (fri, mon):
        for i in range(n):
            price = 100.0 + i * 0.1
            rows.append(Bar("TEST", "5 mins", base + i * 300, price,
                            price + 0.25, price - 0.25, price + 0.05,
                            1000.0 + i))
    return rows


def _is_weekend_et(ts: int) -> bool:
    """True when ``ts`` falls on a Saturday or Sunday in New York time."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    et = datetime.fromtimestamp(int(ts), tz=ZoneInfo("America/New_York"))
    return et.weekday() >= 5


@pytest.mark.parametrize("ext_hours", [False, True])
def test_two_session_gap_collapses_instead_of_padding_the_weekend(ext_hours):
    """Q-22 regression: a between-session gap is not a hole.

    Pre-fix the series carried 904 ``ts`` slots for 80 bars — 824
    placeholders, every weekend period among them — so the candles clustered
    at the two edges of a multi-day axis. The hole decision is the
    non-trading authority, not an index jump: a gap that crosses a session
    boundary contributes no placeholder slots (AC-D21.4.1), while a hole
    inside one session still does (AC-D21.4.4, the 900 s case below).
    """
    bars = _two_session_bars()
    candles = LV.series_ops("candles", bars, "5 mins", ext_hours)[0]
    ts = candles["cols"]["ts"]
    closes = candles["cols"]["close"]

    assert [t for t, c in zip(ts, closes) if c is not None] == [b.ts for b in bars]
    placeholders = [t for t, c in zip(ts, closes) if c is None]
    assert [t for t in placeholders if _is_weekend_et(t)] == [], (
        "the weekend must contribute no whitespace slots"
    )
    assert placeholders == [], (
        f"{len(placeholders)} placeholder slots for {len(bars)} bars across a "
        "session boundary: the gap is not a within-session hole"
    )
    assert len(ts) == len(bars) == 80
    assert ts == [b.ts for b in bars]


@pytest.mark.parametrize("ext_hours", [False, True])
def test_weekend_only_gap_keeps_zero_placeholders(ext_hours):
    """AC-D21.4.1 on a clean weekend: Friday's close meets Monday's open.

    40 bars ending at Friday 15:55 ET + 40 from Monday 09:30 ET. The gap is
    entirely closed market time, so it collapses to adjacent bars.
    """
    from datetime import datetime, timezone

    fri_last = int(datetime(2026, 10, 23, 19, 55, tzinfo=timezone.utc).timestamp())
    mon_open = int(datetime(2026, 10, 26, 13, 30, tzinfo=timezone.utc).timestamp())
    bars = []
    for base in (fri_last - 39 * 300, mon_open):
        for i in range(40):
            price = 100.0 + i * 0.1
            bars.append(Bar("TEST", "5 mins", base + i * 300, price,
                            price + 0.25, price - 0.25, price + 0.05,
                            1000.0 + i))
    candles = LV.series_ops("candles", bars, "5 mins", ext_hours)[0]
    ts = candles["cols"]["ts"]

    assert len(ts) == 80
    assert candles["cols"]["close"].count(None) == 0
    assert ts == [b.ts for b in bars]


def test_two_session_set_bars_op_has_one_slot_per_bar(qapp):
    """The measured real path: ``set_series`` → ``bridge.flush()``.

    The wire op must carry 80 ``ts`` slots (one per bar, no placeholders), not
    the 904 the pre-fix tree emitted.
    """
    view = LV.LwcChartView(tz_offset=14400)
    view.set_timeframe("5 mins")
    view.bridge.set_ready(True)
    bars = _two_session_bars()

    view.set_series("candles", bars)
    env = view.bridge.flush()

    candles = env["ops"][0]
    assert candles["op"] == "set_bars"
    assert len(candles["cols"]["ts"]) == 80
    assert candles["cols"]["close"].count(None) == 0
    assert candles["cols"]["ts"] == [b.ts for b in bars]


@pytest.fixture()
def app():
    if APP is None:  # pragma: no cover — gated case skips first
        pytest.skip("no QApplication — QtWebEngine is unavailable here")
    if not APP.arguments():
        pytest.skip(
            "the session QApplication was created with an empty argv; Chromium "
            "aborts on the first profile, so the e2e test cannot run in this "
            "process"
        )
    return APP


@pytest.fixture()
def make_view(app):
    """Build a real ``LwcChartView`` and guarantee a clean teardown."""
    views = []

    def _make():
        view = LV.LwcChartView()
        views.append(view)
        return view

    yield _make
    for view in reversed(views):
        _teardown_view(app, view)


@pytest.mark.webengine
@needs_webengine
def test_update_chart_reaches_the_page_through_the_real_transport(app, make_view):
    """The acceptance for Q-19: real view + host + ``update_chart(bars)``.

    The only assertion source is the page's own snapshot through
    ``runJavaScript`` — no ``host.resize``, no ``lwApplyOps``, no envelope
    captured in Python. On the pre-Q-19 tree the snapshot stays empty (the
    page never subscribed and the replay raced the QWebChannel setup), so the
    wait below times out; the fixed tree lands the plotted bar count.
    """
    view = make_view()
    # Real geometry before the page exists: the axis' visible range and its
    # rendered tick labels need a laid-out viewport (see ``_layout_page``).
    view.resize(950, 850)
    _layout_page(view)
    host = view.ensure_host()

    # The page subscribes to the JSON channel and then calls bridge.pageReady();
    # nothing else may declare the transport ready (S3d).
    _wait_until(
        app, lambda: view.bridge.is_ready, 30_000,
        "the page to subscribe and call bridge.pageReady()",
    )

    bars = _bars()
    view.update_chart(bars)  # the real ChartPanel spelling, real bridge

    expected = len(view.plotted_bars)
    assert expected == len(bars) > 0

    _wait_until(
        app, lambda: len(_candles(host)) == expected, 20_000,
        "window.lwSnapshot().candles.length to equal the plotted bar count",
    )

    rows = _candles(host)
    assert len(rows) == expected, (
        f"the page holds {len(rows)} candles, the view plotted {expected} — "
        "the bars did not cross the real transport"
    )
    # The right rows, not just the right count. Q-20: the page's series time
    # is the bar's real UTC timestamp — a logical index here is exactly the
    # 1970 axis the owner's screenshot showed.
    assert rows[0]["time"] == bars[0].ts, (
        f"first series time {rows[0]['time']!r} is not the first bar ts "
        f"{bars[0].ts!r}")
    assert rows[-1]["time"] == bars[-1].ts
    assert rows[-1]["close"] == pytest.approx(bars[-1].close)

    # The page fits the series to its laid-out width (a fit at width 0 leaves
    # the library's default tail view), so wait for that fit before reading
    # the scale — the assertions below still check real values.
    _wait_until(app, lambda: _axis(host).get("from") == bars[0].ts, 10_000,
                "the page's time axis to fit the loaded series")

    probe = _axis(host)
    assert probe, "window.lwAxisProbe() is missing from the page"
    assert probe["firstTime"] == bars[0].ts
    assert probe["lastTime"] == bars[-1].ts
    # The time scale's own visible range is real time, not 0..N-1.
    assert probe["from"] == bars[0].ts
    assert probe["to"] == bars[-1].ts

    # A rendered tick label names the bar's real date (2023-11-14 UTC here),
    # never 01/01. `firstLabel` is the axis formatter wired into the chart ...
    expected_label = LV.format_tz_label(bars[0].ts, view.tz_offset)
    assert probe["firstLabel"] == expected_label
    assert not probe["firstLabel"].startswith("01/01"), (
        f"the axis still reads as epoch-zero: {probe['firstLabel']!r}")
    assert probe["firstLabel"].startswith("11/14")
    # ... and every tick the library actually rendered agrees with it.
    assert probe["ticks"], "the time axis produced no tick label at all"
    for tick in probe["ticks"]:
        assert tick["label"] == LV.format_tz_label(tick["time"],
                                                   view.tz_offset), tick
        assert not tick["label"].startswith("01/01")


@pytest.mark.webengine
@needs_webengine
def test_all_five_modes_reach_the_page_through_the_real_transport(app, make_view):
    """Parity row 1 re-proof: every render mode crosses the real transport."""
    view = make_view()
    host = view.ensure_host()
    _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                "the page to call bridge.pageReady()")

    bars = _bars(120)
    view.resize(950, 850)
    view.update_chart(bars)
    expected = len(view.plotted_bars)
    _wait_until(app, lambda: len(_candles(host)) == expected, 20_000,
                "the candle history to cross the transport")

    for mode in LV.MODES[1:]:
        view.set_mode(mode)
        _wait_until(
            app, lambda m=mode: _run_js(host, "window.lwActiveMode()") == m,
            10_000,
            f"the page to switch to {mode!r} through the real transport",
        )
        assert len(_candles(host)) == expected, (
            f"{mode!r} mode changed the candle count on the page"
        )


@pytest.mark.webengine
@needs_webengine
def test_live_tick_crosses_the_real_transport_without_a_history_rebuild(app, make_view):
    """Parity row 2 re-proof: a live tick updates the forming bar in place."""
    view = make_view()
    host = view.ensure_host()
    _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                "the page to call bridge.pageReady()")

    bars = _bars(60)
    view.resize(950, 850)
    view.update_chart(bars)
    expected = len(view.plotted_bars)
    _wait_until(app, lambda: len(_candles(host)) == expected, 20_000,
                "the candle history to cross the transport")

    last = bars[-1]
    tick = Bar("TEST", "5 mins", last.ts, last.open, last.high + 0.5,
               last.low, last.close + 1.0, last.volume + 10.0)
    view.update_last_bar(tick, False)
    _wait_until(
        app, lambda: abs(_candles(host)[-1]["close"] - tick.close) < 1e-9,
        10_000,
        "the forming bar's close to update through the real transport",
    )
    assert len(_candles(host)) == expected, (
        "an intra-bar tick rebuilt the history instead of updating in place"
    )

    new_bar = Bar("TEST", "5 mins", last.ts + 60, tick.close,
                  tick.close + 0.5, tick.close - 0.5, tick.close, 2000.0)
    view.update_last_bar(new_bar, True)
    _wait_until(app, lambda: len(_candles(host)) == expected + 1, 10_000,
                "a new period to append exactly one candle on the page")
    # Q-20: the appended bar's series time is its own timestamp.
    assert _candles(host)[-1]["time"] == new_bar.ts


@pytest.mark.webengine
@needs_webengine
def test_within_session_hole_keeps_its_whitespace_slots_on_the_page(app,
                                                                    make_view):
    """AC-D21.4.4 through the real page: a hole is empty space, not a bar.

    The series times are the bars' real timestamps (the axis shows the gap's
    dates) while the two missing periods cross as whitespace placeholders.
    The page's snapshot keeps the real bars only, so a placeholder can never
    inflate a bar count.
    """
    view = make_view()
    host = view.ensure_host()
    _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                "the page to call bridge.pageReady()")

    view.resize(950, 850)
    view.set_timeframe("5 mins")
    bars = _rth_bars_with_hole()
    view.update_chart(bars)
    expected = len(view.plotted_bars)
    assert expected == len(bars)

    _wait_until(app, lambda: len(_candles(host)) == expected, 20_000,
                "the holed history to cross the transport")
    rows = _candles(host)
    assert [r["time"] for r in rows] == [b.ts for b in bars]
    # The hole is real: the fixture omits bars 4 and 5, so the row at
    # timestamp base+1800 (bar 6) follows the one at base+900 (bar 3) by
    # three periods — two missing 300 s slots in between.
    assert rows[4]["time"] - rows[3]["time"] == 3 * 300
    # The logical axis still exists internally and is not the wire time.
    assert view.logical_index[-1] > expected - 1
    assert view.series_times == [b.ts for b in bars]


@pytest.mark.webengine
@needs_webengine
def test_page_messages_reach_python_signals(app, make_view):
    """Q-20: a drawing commit / selection / alarm / key raised *in the page*
    reaches the Python surface MainWindow wires.

    The page's own modules call these bridge slots (``primitives.js`` ->
    ``drawingCommitted``, ``alarms.js`` -> ``alarmCreated``, ``chart.js`` ->
    ``keyPressed``); with only two slots existing, every one of these calls
    was silently dropped and the tools looked dead. A count of rendered
    drawings would not prove the path — this asserts the signal and its
    payload.
    """
    view = make_view()
    host = view.ensure_host()
    _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                "the page to call bridge.pageReady()")

    bars = _bars(60)
    view.resize(950, 850)
    view.update_chart(bars)
    _wait_until(app, lambda: len(_candles(host)) == len(view.plotted_bars),
                20_000, "the candle history to cross the transport")

    created, selections, alarms, keys, updates, deleted = [], [], [], [], [], []
    view.drawing_controller.created.connect(created.append)
    # ``updated`` carries three arguments (id, payload, colour): PyQt would
    # silently drop two when connecting straight to ``list.append``.
    view.drawing_controller.updated.connect(
        lambda drawing_id, payload, color: updates.append(
            (drawing_id, payload, color)))
    view.drawing_controller.deleted.connect(deleted.append)
    view.drawing_controller.selection_changed.connect(selections.append)
    view.alarm_controller.create_requested.connect(alarms.append)
    view.key_pressed.connect(keys.append)

    plotted = view.plotted_bars
    _call_slot(host, "drawingCommitted", {
        "kind": "trendline",
        "points": [[2.0, 100.5], [7.0, 102.25]],
        "color": "#ff8800",
    })
    _wait_until(app, lambda: created, 5_000,
                "the page's drawing commit to reach drawing_controller.created")
    drawing = created[0]
    assert drawing.kind == "trendline"
    assert drawing.symbol == "TEST"
    assert drawing.color == "#ff8800"
    # The page's fractional anchors come back as bar timestamps on the
    # plotted axis — the same domain the store and the fan-out use.
    assert drawing.payload["p1"]["x"] == plotted[2].ts
    assert drawing.payload["p2"]["x"] == plotted[7].ts
    assert drawing.payload["p1"]["y"] == pytest.approx(100.5)
    assert drawing.payload["p2"]["y"] == pytest.approx(102.25)

    _call_slot(host, "selectionChanged", {"id": 3})
    _wait_until(app, lambda: selections, 5_000,
                "the page's selection to reach drawing_controller")
    assert selections == [3]

    _call_slot(host, "alarmCreated", {"price": 101.25})
    _wait_until(app, lambda: alarms, 5_000,
                "the page's alarm to reach alarm_controller.create_requested")
    assert alarms == [pytest.approx(101.25)]

    _call_slot(host, "keyPressed", {"key": "ArrowLeft"})
    _wait_until(app, lambda: keys, 5_000,
                "the page's key to reach the view's key_pressed signal")
    assert keys == ["ArrowLeft"]

    # The remaining messages are reachable too (slots + re-emit, not just
    # present on the bridge).
    _call_slot(host, "drawingDeleted", {"id": 3})
    _wait_until(app, lambda: deleted, 5_000,
                "the page's delete to reach drawing_controller.deleted")
    assert deleted == [3]
    _call_slot(host, "drawingUpdated", {
        "id": 3, "kind": "horizontal", "price": 102.0})
    _wait_until(app, lambda: updates, 5_000,
                "the page's edit to reach drawing_controller.updated")
    drawing_id, payload, color = updates[0]
    assert drawing_id == 3
    assert payload["y"] == pytest.approx(102.0)
    assert color == ""

    refused = []
    view.zoom_refused.connect(lambda: refused.append(True))
    _call_slot(host, "zoomRefused", {"trigger": "enter_zoom"})
    _wait_until(app, lambda: refused, 5_000,
                "the page's zoom refusal to reach zoom_refused")
    assert refused == [True]


# ── Q-23: the owner's real AAPL history, judged on the page's own bitmap ──

MANUAL_REAL_DATA = (
    "manual: run this on the owner's box with the AAPL 5-min cache present "
    "and confirm the chart shows candles (not full-height stripes) — Q-23"
)

#: Bitmap capture needs a real rasteriser. An offscreen platform runs the page
#: and answers ``runJavaScript`` for real (every probe below works), but
#: QtWebEngine never paints there: ``takeScreenshot`` returns a blank canvas
#: (Q-15). Only the pixel assertions are gated; the probes run everywhere.
COCOA_BITMAP_COMMAND = (
    "QT_QPA_PLATFORM=cocoa .venv/bin/python -m pytest "
    "tests/test_lwc_e2e_data.py::"
    "test_real_aapl_history_captures_a_readable_candle_field_bitmap -q"
)
#: The effective platform after the module-level ``setdefault`` above; an
#: unset environment is offscreen here.
_PLATFORM = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
needs_rasteriser = pytest.mark.skipif(
    _PLATFORM in ("", "offscreen", "minimal"),
    reason=(
        "QtWebEngine cannot rasterise under an offscreen platform (Q-15): "
        "takeScreenshot returns a blank canvas, so the bitmap cannot be "
        "judged here. Run on a display: " + COCOA_BITMAP_COMMAND
    ),
)

#: The owner's measured acceptance series: 5,952 AAPL 5-minute bars.
REAL_SYMBOL = "AAPL"
REAL_TIMEFRAME = "5 mins"
REAL_MIN_BARS = 5000


def _real_aapl_bars() -> list:
    """Read the owner's real AAPL 5-min cache (read-only, no store writes).

    Uses a read-only SQLite URI rather than ``BarCache`` so this test never
    opens the application database for writing and never needs the production
    opt-in. An absent/corrupt cache yields ``[]`` and the case skips.
    """
    import sqlite3

    from config import paths

    db_path = paths.production_db_path()
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT ts, open, high, low, close, volume FROM bars "
                "WHERE symbol=? AND timeframe=? AND ext_hours=1 "
                "ORDER BY ts ASC",
                (REAL_SYMBOL, REAL_TIMEFRAME),
            ).fetchall()
        finally:
            conn.close()
    except Exception:
        return []
    return [Bar(REAL_SYMBOL, REAL_TIMEFRAME, *row) for row in rows]


def _candle_bitmap_stats(image) -> dict:
    """Count candle-coloured columns and their vertical extents.

    A stripe field paints nearly every column from top to bottom: the body
    share of the pitch is 65 %, so in a real candle field most columns are
    background and the coloured ones have varied heights. The price pane is
    the top 85 % (the volume histogram owns the bottom 15 %).
    """
    from PyQt6.QtGui import QImage

    image = image.convertToFormat(QImage.Format.Format_RGB32)
    width, height = image.width(), image.height()
    stride = image.bytesPerLine()
    bits = image.constBits()
    bits.setsize(image.sizeInBytes())
    data = bytes(bits)
    price_bottom = max(1, int(height * 0.85))
    columns = 0
    stripes = 0
    extents: list = []
    for x in range(width):
        low = None
        high = None
        for y in range(price_bottom):
            offset = y * stride + x * 4
            b = data[offset]
            g = data[offset + 1]
            r = data[offset + 2]
            # #34d399 (up) / #f87171 (down), near-exact: antialiased edges
            # differ enough that only the body interior counts.
            up = abs(r - 52) < 36 and abs(g - 211) < 36 and abs(b - 153) < 36
            down = abs(r - 248) < 36 and abs(g - 113) < 36 and abs(b - 113) < 36
            if not (up or down):
                continue
            if low is None or y < low:
                low = y
            if high is None or y > high:
                high = y
        if low is None:
            continue
        columns += 1
        extent = high - low + 1
        extents.append(extent)
        if extent >= 0.8 * price_bottom:
            stripes += 1
    return {
        "width": width,
        "height": height,
        "columns": columns,
        "column_fraction": (columns / width) if width else 0.0,
        "stripes": stripes,
        "stripe_fraction": (stripes / width) if width else 0.0,
        "extents": extents,
    }


def _real_aapl_page(app, make_view) -> tuple:
    """Load the owner's cached AAPL history into a real, laid-out page (Q-23).

    Shared setup for the two acceptance cases: the probe case reads the page's
    own answers, the display-only case captures its bitmap. Returns
    ``(host, expected_bar_count)``; the ``make_view`` fixture keeps the view
    alive and dismantles it. An absent cache skips both cases.
    """
    bars = _real_aapl_bars()
    if len(bars) < REAL_MIN_BARS:
        pytest.skip(
            f"the owner's {REAL_SYMBOL} {REAL_TIMEFRAME} cache is not present "
            f"here ({len(bars)} bars) — " + MANUAL_REAL_DATA
        )

    view = make_view()
    view.resize(1200, 800)
    _layout_page(view)
    host = view.ensure_host()
    _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                "the page to call bridge.pageReady()")

    view.set_timeframe(REAL_TIMEFRAME)
    view.update_chart(bars)
    expected = len(view.plotted_bars)
    assert expected == len(bars), "the whole cached series must be plotted"
    _wait_until(app, lambda: len(_candles(host)) == expected, 30_000,
                "the real AAPL history to cross the transport")

    def probe() -> dict:
        return _axis(host)

    _wait_until(
        app,
        lambda: (probe().get("barSpacing") or 0) > 0
        and (probe().get("chartWidth") or 0) > 0
        and probe().get("needsFit") is False,
        30_000,
        "the chart to be laid out and fitted at a real width",
    )
    return host, expected


@pytest.mark.webengine
@needs_webengine
def test_real_aapl_history_renders_a_readable_candle_field(app, make_view):
    """Q-23 acceptance on the owner's real data: the page's own answers.

    Loads the actual AAPL 5-minute cache (5,952 bars) through
    ``LwcChartView``, waits for layout, then reads the page's own probes: a
    positive ``barSpacing`` (the measured failure was 0), a narrowed visible
    window (not thousands of sub-pixel bars) and a real volume ceiling (not
    the 100 floor). JavaScript answers under offscreen, so this half runs
    everywhere; only the rasterised bitmap is gated by ``needs_rasteriser``.
    """
    host, expected = _real_aapl_page(app, make_view)

    probe_now = _axis(host)
    assert probe_now["barSpacing"] > 0, (
        f"barSpacing is {probe_now['barSpacing']!r}: the fit ran at a zero "
        "width (the Q-23 stripe cause)"
    )
    assert probe_now["containerWidth"] > 0
    assert probe_now["chartWidth"] > 0
    # A readable newest window: thousands of bars at sub-pixel spacing is a
    # barcode, so the visible range is narrower than the series.
    logical = probe_now["logical"]
    assert logical is not None
    assert logical["to"] - logical["from"] < expected, probe_now

    volume = _run_js(host, "window.lwVolumeRange()")
    assert isinstance(volume, dict), volume
    assert volume["minValue"] == 0
    assert volume["maxValue"] > 100, (
        f"lwVolumeRange() still reads the {volume['maxValue']!r} floor: no "
        "visible bar priced the volume pane"
    )


@pytest.mark.webengine
@needs_webengine
@needs_rasteriser
def test_real_aapl_history_captures_a_readable_candle_field_bitmap(
        app, make_view, tmp_path):
    """Q-23's pixel half: the real page renders candles, not stripes.

    Same real cache and transport as the probe case, then a bitmap captured on
    the page and judged for candle bodies and wicks. Gated on a rasterising
    platform only (Q-15): the assertions themselves are unchanged, so on a
    display a stripe field still fails.
    """
    import base64

    from PyQt6.QtCore import QByteArray
    from PyQt6.QtGui import QImage

    host, _expected = _real_aapl_page(app, make_view)

    data_url = _run_js(
        host,
        """
        (function () {
          if (typeof window.lwTakeScreenshot !== "function") return null;
          var canvas = window.lwTakeScreenshot();
          return canvas ? canvas.toDataURL("image/png") : null;
        })()
        """,
        20_000,
    )
    assert isinstance(data_url, str) and data_url.startswith(
        "data:image/png;base64,"), "the page produced no bitmap to judge"
    image = QImage.fromData(
        QByteArray(base64.b64decode(data_url.split(",", 1)[1])))
    assert not image.isNull()
    shot = tmp_path / "q23_aapl_5min.png"
    assert image.save(str(shot))
    stats = _candle_bitmap_stats(image)
    assert stats["columns"] > 10, f"no candles in the captured bitmap: {stats}"
    assert stats["column_fraction"] < 0.9, (
        "nearly every column is candle-coloured — the stripe field is back: "
        f"{stats}"
    )
    assert stats["stripe_fraction"] < 0.05, (
        "columns run the full price-pane height — full-height stripes, not "
        f"candles: {stats['stripes']} of {stats['width']} columns ({shot})"
    )
    assert len(set(stats["extents"])) > 10, (
        "every candle column has the same height — not a candle field: "
        f"{sorted(set(stats['extents']))[:10]} ({shot})"
    )



# ---------------------------------------------------------------------------
# Q-31 — the non-bar channels cross the *real* transport
#
# Before Q-31 the page loaded only chart.js: ``alarms.js`` / ``primitives.js``
# / ``overlays.js`` / ``studies.js`` / ``interaction.js`` never ran, and the
# view's five channel signals had no consumer, so nothing but bars ever
# reached the page. These cases drive the real view and read the page's own
# module state back — the assertion that would have caught both a missing
# script tag and an envelope the module validators reject.
# ---------------------------------------------------------------------------


def _channel_view(make_view, bars):
    view = make_view()
    view.set_symbol("AAPL")
    view.set_timeframe("5 mins")
    view.ensure_host()
    _layout_page(view)
    _pump(APP, 3000)
    view.update_chart(bars)
    _pump(APP, 600)
    return view


def test_the_page_loads_every_channel_module(qapp, make_view):
    """All five modules are present in the loaded page, not merely on disk."""
    bars = _two_session_bars()
    view = _channel_view(make_view, bars)
    host = view._host
    modules = _run_js(host, "window.lwModules ? window.lwModules() : null")
    assert isinstance(modules, dict), "the page exposes no module probe"
    assert modules == {
        "interaction": True, "alarms": True, "primitives": True,
        "overlays": True, "studies": True,
    }, modules
    handles = _run_js(host, "Object.keys(window.lwHandles())")
    assert "chart" in handles and "price" in handles, handles


def test_alarm_preview_crosses_and_the_page_draws_it(qapp, make_view):
    """``show_alarm_preview`` → bridge channel → the page's own price line.

    The pre-Q-31 tree never emitted the channel at all; a channel emitted with
    the transport's ``channel`` key still fails here, because every module
    validator accepts exactly ``{v, ops}``.
    """
    bars = _two_session_bars()
    view = _channel_view(make_view, bars)
    host = view._host

    view.show_alarm_preview(123.45)
    _pump(APP, 700)
    preview = _run_js(host, "window.LwAlarms.snapshot().preview")
    assert isinstance(preview, dict), "the page drew no alarm preview line"
    assert float(preview["price"]) == 123.45

    view.hide_alarm_preview()
    _pump(APP, 500)
    assert _run_js(host, "window.LwAlarms.snapshot().preview") is None


def test_drawings_channel_renders_real_records(qapp, make_view):
    """A stored ``Drawing`` reaches the page's render plan.

    Uses the model objects the session fans out (``drawing_op`` reads
    attributes, not dict keys), so this fails if the wire ever carries the
    record instead of the validated item.
    """
    from data.models import Drawing

    bars = _two_session_bars()
    view = _channel_view(make_view, bars)
    host = view._host
    start = bars[0].ts

    view.set_drawings([
        Drawing(symbol="AAPL", kind="horizontal", payload={"y": 120.5}, id=7),
        Drawing(symbol="AAPL", kind="trendline",
                payload={"p1": {"x": start + 300, "y": 104.0},
                         "p2": {"x": start + 3000, "y": 110.0}}, id=8),
    ])
    _pump(APP, 800)
    assert len(view.drawing_items) == 2
    assert _run_js(host, "window.LwPrimitives.snapshot().items.length") == 2
    plan = _run_js(host, "window.LwPrimitives.snapshot().plan")
    assert isinstance(plan, dict) and plan["hlines"], plan


def test_the_uploaded_router_state_follows_python(qapp, make_view):
    """The interaction channel carries the frozen router's mode to the page."""
    bars = _two_session_bars()
    view = _channel_view(make_view, bars)
    host = view._host

    view.set_alarm_mode(True)
    _pump(APP, 500)
    state = _run_js(host, "window.lwRouterState()")
    assert state["mode"] == "ALARM_PLACING", state

    view.set_alarm_mode(False)
    _pump(APP, 400)
    assert _run_js(host, "window.lwRouterState()")["mode"] == "IDLE"


# ---------------------------------------------------------------------------
# Q-32 — ALARM MODE end-to-end: a page click in ALARM_PLACING creates an alarm
#
# Q-31 made the mode *arm*: the interaction channel crosses, `chart.js`
# mirrors it, and the page reports ALARM_PLACING — yet nothing converted a
# click into an alarm, so the mode was a decoration. These cases dispatch real
# `PointerEvent`s on the page's `#chart` container (the same target a real
# mouse event bubbles through on its way out of the library's canvas) and
# assert the whole path: gesture -> `alarmCreated` bridge slot ->
# `_on_page_alarm_created` -> `alarm_controller.create_requested`. They also
# pin the two things the fix must not break: pan/zoom suppression applies
# *only* while placing and is restored afterwards, and a click after disarming
# creates nothing.
# ---------------------------------------------------------------------------


def _chart_rect(host) -> dict:
    """The page's laid-out ``#chart`` box (rect + offset)."""
    rect = _run_js(
        host,
        """
        (function () {
          var el = document.getElementById("chart");
          if (!el) return null;
          var r = el.getBoundingClientRect();
          return {
            top: r.top, left: r.left,
            width: r.width, height: r.height
          };
        })()
        """,
    )
    return rect if isinstance(rect, dict) else {}


def _pointer(host, kind: str, x: float, y: float):
    """Dispatch one real ``PointerEvent`` at ``(x, y)`` inside ``#chart``.

    ``x``/``y`` are offsets inside the container, so the case is independent of
    where the page sits; the event is the browser's own ``PointerEvent``
    constructor, dispatched through the DOM — not a synthetic call into the
    gesture module.
    """
    js = """
    (function () {
      var el = document.getElementById("chart");
      if (!el) return false;
      var r = el.getBoundingClientRect();
      el.dispatchEvent(new PointerEvent(%s, {
        bubbles: true, cancelable: true, composed: true,
        clientX: r.left + %r, clientY: r.top + %r,
        pointerId: 1, pointerType: "mouse", isPrimary: true,
        button: 0, buttons: %d
      }));
      return true;
    })()
    """ % (json.dumps(kind), float(x), float(y), 0 if kind == "pointerup" else 1)
    return _run_js(host, js)


def _record_pan_zoom_options(host) -> bool:
    """Record the chart's own ``handleScroll`` / ``handleScale`` applications.

    ``IChartApi.options()`` is not part of the vendored surface this page is
    allowed to depend on, so the acceptance observes the *calls* the gesture
    layer makes on the real chart handle — the library's own contract for
    turning its pan/zoom off and back on.
    """
    return _run_js(
        host,
        """
        (function () {
          var handles = window.lwHandles ? window.lwHandles() : null;
          var chart = handles && handles.chart;
          if (!chart || typeof chart.applyOptions !== "function") return false;
          if (chart.__q32Applied) return true;
          var original = chart.applyOptions;
          chart.__q32Applied = [];
          chart.applyOptions = function (options) {
            if (options
                && ("handleScroll" in options || "handleScale" in options)) {
              chart.__q32Applied.push({
                handleScroll: options.handleScroll,
                handleScale: options.handleScale
              });
            }
            return original.apply(chart, arguments);
          };
          return true;
        })()
        """,
    )


def test_alarm_mode_click_creates_an_alarm_through_the_real_page(qapp,
                                                                make_view):
    """Q-32 acceptance: ALARM_PLACING + a real click -> ``create_requested``.

    The page's own price mapping is the expectation: the preview line the
    pointer drew carries the price the click reported, so a gesture that
    quietly used a stale/zero price fails here. After disarming, the same
    click must create nothing and the preview must stay gone.
    """
    bars = _two_session_bars()
    view = _channel_view(make_view, bars)
    # The demo chart is 200x100 at the view's default size; give the pointer
    # cases a real price pane to click in (the page re-sizes through its own
    # ResizeObserver, the Q-23 path).
    view.resize(960, 720)
    _pump(APP, 800)
    host = view._host

    created = []
    view.alarm_controller.create_requested.connect(created.append)

    assert _record_pan_zoom_options(host) is True, (
        "the page exposes no chart handle to observe"
    )

    # ── arm: mode mirrored, crosshair on, the library's pan/zoom off ──────
    view.set_alarm_mode(True)
    _pump(APP, 600)
    armed = _run_js(host, "window.lwGestureState ? window.lwGestureState() : null")
    assert isinstance(armed, dict), "the page exposes no gesture state probe"
    assert armed["mode"] == "ALARM_PLACING", armed
    assert armed["alarmMode"] is True, armed
    assert _run_js(host, "document.getElementById('chart').style.cursor") == (
        "crosshair"), "ALARM_PLACING did not set the placement cursor"
    applied = _run_js(host, "window.lwHandles().chart.__q32Applied")
    assert applied and applied[-1] == {
        "handleScroll": False, "handleScale": False,
    }, f"the library's pan/zoom was not suppressed while placing: {applied}"

    rect = _chart_rect(host)
    assert rect and rect["width"] > 100 and rect["height"] > 100, rect
    x = rect["width"] / 2.0
    y = rect["height"] / 3.0  # the price pane (volume owns the bottom 15 %)

    # ── move: the yellow preview follows the pointer's own price ──────────
    _pointer(host, "pointerdown", x, y)
    _pointer(host, "pointermove", x, y)
    preview_price = _run_js(host, "window.lwGestureState().previewPrice")
    assert isinstance(preview_price, (int, float)), (
        f"the pointer did not map to a price: {preview_price!r}"
    )
    preview_line = _run_js(host, "window.LwAlarms.snapshot().preview")
    assert isinstance(preview_line, dict), "the page drew no alarm preview line"
    assert float(preview_line["price"]) == pytest.approx(preview_price)

    # ── click: the gesture becomes the Python create request ──────────────
    _pointer(host, "pointerup", x, y)
    _wait_until(APP, lambda: created, 5_000,
                "the page's ALARM_PLACING click to reach create_requested")
    assert len(created) == 1, created
    price = float(created[0])
    assert price == pytest.approx(float(preview_price)), (
        "the created alarm's price is not the clicked price"
    )
    assert price > 0
    assert min(b.low for b in bars) - 1.0 <= price <= max(
        b.high for b in bars) + 1.0, f"{price} is outside the plotted series"
    assert _run_js(host, "window.LwAlarms.snapshot().preview") is None, (
        "the preview survived the placement"
    )

    # ── disarm: cursor and both pan/zoom handles come back ────────────────
    view.set_alarm_mode(False)
    _pump(APP, 600)
    idle = _run_js(host, "window.lwGestureState()")
    assert idle["mode"] == "IDLE", idle
    assert idle["panZoomSuppressed"] is False, idle
    assert _run_js(host, "document.getElementById('chart').style.cursor") == ""
    applied = _run_js(host, "window.lwHandles().chart.__q32Applied")
    assert applied[-1] == {
        "handleScroll": True, "handleScale": True,
    }, f"pan/zoom was not restored after leaving alarm mode: {applied}"

    # ── a click after disarming creates nothing ───────────────────────────
    _pointer(host, "pointerdown", x, y)
    _pointer(host, "pointermove", x, y)
    _pointer(host, "pointerup", x, y)
    _pump(APP, 500)
    assert len(created) == 1, (
        f"a click after disarming created an alarm: {created}"
    )
    assert _run_js(host, "window.LwAlarms.snapshot().preview") is None

