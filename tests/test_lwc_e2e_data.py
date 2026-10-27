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
display limitation applies only to rasterisation).

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
