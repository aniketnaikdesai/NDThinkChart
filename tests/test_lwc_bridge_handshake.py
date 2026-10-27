"""tests/test_lwc_bridge_handshake.py — Q-16: the page's ``lwBridge`` handshake.

Blank-chart regression, **third cause** (found by looking at the real page,
not by a unit test): ``ui/lwc_host.py::create_host`` never created a
``QWebChannel``, never called ``registerObject("lwBridge", bridge)`` and never
attached the channel with ``page.setWebChannel(...)``. ``chart.html`` loads
``qrc:///qtwebchannel/qwebchannel.js`` and ``chart.js::bindChannel`` runs
``new QWebChannel(qt.webChannelTransport, ...)``, but Qt only injects
``qt.webChannelTransport`` into a page that already had a channel when the
load started. With no channel, ``qt`` is undefined, the callback never runs,
``window.lwBridge`` stays undefined and no op can ever cross. Every existing
test missed it because they inject envelopes through ``window.lwApplyOps`` or
drive the bridge's Python signals directly (``FakeTransport``).

This module is deliberately *not* a pixel test — it needs no display:

* it drives the real ``LwcChartView`` + ``ensure_host()`` (no stub);
* waits for the page's load to reach the Python side
  (``loadFinished`` -> ``bridge.handle_page_ready`` -> ``bridge.is_ready``);
* runs JavaScript in the real page and asserts ``window.lwBridge`` is an
  object — the handshake the broken code never completed;
* asserts the JS object exposes the bridge's transport surface
  (``opsEmitted`` / ``replayFinished`` signal proxies with ``connect``).

The regression fails on the pre-Q-16 host: ``typeof window.lwBridge`` is
``"undefined"`` (the ``qt is not defined`` ReferenceError in ``bindChannel``).
It runs under ``QT_QPA_PLATFORM=offscreen`` in the normal suite; the engine
gate (``HAS_WEBENGINE``) is the only skip — never a display gate (Q-15's
rasterisation limitation does not apply: this test reads JavaScript answers,
not pixels).

``@pytest.mark.webengine`` per DG88/AP-P6-4; a skip names its manual-check
counterpart on a Chromium box.
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui import lwc_host as LH  # noqa: E402
from ui import lwc_view as LV  # noqa: E402

# The ``ndt://`` scheme is honoured only when registered before a
# ``QApplication`` exists (Q-13). Module import happens before any test body
# or conftest fixture constructs one, so this is the earliest safe point.
LH.register_ndt_scheme()

#: The handshake proof has no display requirement; the manual counterpart is
#: for an engine-less box only.
MANUAL_HANDSHAKE = (
    "manual: open the app on a Chromium box and confirm the console has no "
    "'qt is not defined' and window.lwBridge is an object (Q-16 checklist)"
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
    reason="no QtWebEngine here — " + MANUAL_HANDSHAKE,
)


def _pump(app, ms: int) -> None:
    """Run the Qt event loop for ``ms`` milliseconds (no blocking exec_)."""
    from PyQt6.QtCore import QEventLoop

    deadline = time.monotonic() + ms / 1000.0
    while time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        time.sleep(0.01)


_PAGE_DIAG_JS = """
(function () {
  var out = {};
  try { out.readyState = document.readyState; } catch (e) { out.readyState = "unknown"; }
  try { out.lwSnapshot = typeof window.lwSnapshot; } catch (e) { out.lwSnapshot = "unknown"; }
  try { out.lwBridge = typeof window.lwBridge; } catch (e) { out.lwBridge = "unknown"; }
  try {
    out.lwModules = (typeof window.lwModules === "function")
      ? window.lwModules() : (typeof window.lwModules);
  } catch (e) { out.lwModules = "error"; }
  try {
    var el = document.getElementById("chart");
    if (!el) { out.chart = null; }
    else {
      var r = el.getBoundingClientRect();
      out.chart = { w: el.clientWidth, h: el.clientHeight,
        rect: { top: r.top, left: r.left, width: r.width, height: r.height } };
    }
  } catch (e) { out.chart = "error"; }
  return out;
})()
"""


def _collect_page_diagnostics(host=None, view=None) -> str:
    """Best-effort page-load bundle appended to a timed-out readiness wait.

    Uses the explicitly passed ``host``/``view`` when given, else the
    calling test's ``host``/``view`` locals (best-effort). Never raises:
    any failure yields ``"diagnostics unavailable"`` (or a partial bundle
    naming what could not be read). The caller truncates.
    """
    import inspect

    try:
        if host is None or view is None:
            frame = None
            try:
                frame = inspect.currentframe()
                caller = frame.f_back.f_back if frame and frame.f_back else None
                names = dict(getattr(caller, "f_locals", {}) or {})
                if host is None:
                    host = names.get("host")
                if view is None:
                    view = names.get("view")
            except Exception:
                pass
            finally:
                del frame
        if host is None and view is None:
            return "diagnostics unavailable"
        bundle = {}
        if host is not None:
            try:
                bundle["page"] = _run_js(host, _PAGE_DIAG_JS, 3000)
            except Exception as exc:
                bundle["page"] = f"<unavailable: {type(exc).__name__}>"
        else:
            bundle["page"] = "<no host>"
        try:
            bridge = getattr(view, "bridge", None) if view is not None else None
            bundle["bridge_is_ready"] = getattr(bridge, "is_ready", "<no view>")
        except Exception:
            bundle["bridge_is_ready"] = "<unavailable>"
        return str(bundle)[:1500]
    except Exception:
        return "diagnostics unavailable"


def _wait_until(app, predicate, timeout_ms: int, what: str,
                host=None, view=None) -> None:
    from PyQt6.QtCore import QEventLoop

    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        if predicate():
            return
        time.sleep(0.01)
    try:
        diagnostics = _collect_page_diagnostics(host=host, view=view)
    except Exception:
        diagnostics = "diagnostics unavailable"
    raise AssertionError(
        f"timed out after {timeout_ms} ms waiting for {what}"
        f" | page diagnostics: {diagnostics}"
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
    """No-op: the profile wiring is application-lifetime (Q-40).

    ``create_host`` installs the shared ``ndt://`` handler and the
    deny-default interceptor ONCE, parented to the ``QApplication``. Removing
    them here dangled the profile-global registration after the first
    create/destroy cycle (a dead wrapper defeats the ``is None`` reinstall
    guard) and every later page load silently never finished. Teardown must
    leave the shared pair installed.
    """


def _teardown_view(app, view) -> None:
    """Deterministically dismantle the real host (Q-15/Q-16).

    Runs from the fixture finaliser, so a failing handshake reports instead of
    taking the interpreter down at exit. Order: stop the page, drop the
    bridge's Python signal listeners, release the profile wiring, delete the
    widgets/page, drain deferred deletes.
    """
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
        for name in ("opsEmitted", "replayFinished"):
            signal = getattr(bridge, name, None)
            if signal is None:
                continue
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):  # nothing connected / gone
                pass

    # Q-40: the profile wiring is application-lifetime — teardown must NOT
    # remove the shared handler/interceptor (see _release_profile).

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


#: How long the page/bridge readiness probe may wait for a trivial page load
#: plus a JS round-trip before declaring this Chromium nonfunctional. One
#: short cached wait per session — not one 30 s ``_wait_until`` timeout per
#: test (a present-but-nonfunctional offscreen engine otherwise burns 30 s
#: per case before failing).
_READINESS_TIMEOUT_MS = 10_000

#: Tri-state cache for the readiness probe: None = unprobed, True/False after
#: the single probe. A passing session pays the probe once; later tests skip
#: it entirely.
_READINESS_CACHE: object = None


def _probe_page_answers(app, timeout_ms: int = _READINESS_TIMEOUT_MS) -> bool:
    """True when a trivial page loads and answers JS in this process."""
    from PyQt6.QtCore import QEventLoop, QTimer

    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except Exception:
        return False
    view = None
    try:
        view = QWebEngineView()
        loaded = QEventLoop()
        view.loadFinished.connect(lambda _ok: loaded.quit())
        QTimer.singleShot(timeout_ms // 2, loaded.quit)
        view.setHtml("<html><body>ready</body></html>")
        loaded.exec()
        box: dict = {}
        answered = QEventLoop()

        def _done(result):
            box["result"] = result
            answered.quit()

        QTimer.singleShot(timeout_ms // 2, answered.quit)
        try:
            view.page().runJavaScript("1+1", 0, _done)
        except Exception:
            return False
        answered.exec()
        return box.get("result") == 2
    except Exception:
        return False
    finally:
        try:
            if view is not None:
                view.deleteLater()
        except Exception:  # pragma: no cover — teardown must never raise
            pass
        _drain(app)


def _ensure_functional_webengine(app) -> None:
    """Skip when Chromium is present but cannot run a page here.

    Extends the ``needs_webengine`` pattern (which only gates on import-time
    availability): a Chromium-present-but-nonfunctional offscreen environment
    otherwise burns one 30 s ``_wait_until`` timeout per test before failing.
    One cached short probe per session replaces N long timeouts.
    """
    global _READINESS_CACHE
    if _READINESS_CACHE is True:
        return
    if _READINESS_CACHE is False:
        pytest.skip("QtWebEngine loads no page in this process — "
                    + MANUAL_HANDSHAKE)
    if _probe_page_answers(app):
        _READINESS_CACHE = True
        return
    _READINESS_CACHE = False
    pytest.skip(
        "QtWebEngine is present but its renderer answers nothing offscreen "
        "here — " + MANUAL_HANDSHAKE
    )


@pytest.fixture()
def app():
    if APP is None:  # pragma: no cover — gated case skips first
        pytest.skip("no QApplication — QtWebEngine is unavailable here")
    if not APP.arguments():
        pytest.skip(
            "the session QApplication was created with an empty argv; Chromium "
            "aborts on the first profile, so the handshake test cannot run in "
            "this process"
        )
    _ensure_functional_webengine(APP)
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


#: The transport surface the page must find on ``channel.objects.lwBridge``.
#: ``opsEmitted``/``replayFinished`` are the bridge's signals; QtWebChannel
#: exposes each signal as an object with ``connect``/``disconnect``.
BRIDGE_SURFACE_JS = """
(function () {
  var b = window.lwBridge;
  if (!b) return { bridge: typeof b };
  return {
    bridge: typeof b,
    opsEmitted: typeof b.opsEmitted,
    opsEmittedConnect: typeof (b.opsEmitted && b.opsEmitted.connect),
    replayFinished: typeof b.replayFinished,
    replayFinishedConnect: typeof (b.replayFinished && b.replayFinished.connect)
  };
})()
"""


@pytest.mark.webengine
@needs_webengine
def test_page_bridge_handshake_reaches_window(make_view):
    """A real host load publishes ``window.lwBridge`` and the Python side
    sees the page-ready transition (Q-16).

    Fails on the pre-Q-16 host: no channel was attached before ``load``, so
    ``qt.webChannelTransport`` is never injected and ``window.lwBridge`` is
    undefined forever.
    """
    view = make_view()
    host = view.ensure_host()

    assert isinstance(host, LH.LwcHost)
    assert view.ensure_host() is host, "ensure_host must be lazy, not rebuilt"
    assert host._bridge is view.bridge, (
        "the host must expose the view's own bridge object"
    )

    # The channel exists, is held strongly, and is the one on the page.
    channel = getattr(host, "_channel", None)
    assert channel is not None, (
        "the host created no QWebChannel — chart.js's bindChannel has "
        "nothing to connect to (Q-16)"
    )
    assert host._channel is channel, (
        "the host must keep a strong reference to its QWebChannel; "
        "setWebChannel() does not take ownership"
    )
    assert host.page().webChannel() is channel, (
        "page.setWebChannel(channel) was never called — Qt will not inject "
        "qt.webChannelTransport into the page"
    )
    assert LH.BRIDGE_OBJECT_NAME == "lwBridge", (
        "the registered object name must match chart.js's "
        "channel.objects.lwBridge"
    )

    # Python-side page_ready: only loadFinished -> handle_page_ready sets this.
    _wait_until(APP, lambda: view.bridge.is_ready, 30_000,
                "the page load to reach bridge.handle_page_ready "
                "(bridge.is_ready)")
    assert view.bridge.is_ready is True

    # JS-side handshake: the QWebChannel callback assigns window.lwBridge.
    _wait_until(
        APP,
        lambda: _run_js(host, "typeof window.lwBridge") == "object",
        10_000,
        "chart.js bindChannel to publish window.lwBridge "
        "(pre-Q-16: undefined, 'qt is not defined')",
    )

    surface = _run_js(host, BRIDGE_SURFACE_JS)
    assert isinstance(surface, dict), f"bridge surface was {surface!r}"
    assert surface.get("bridge") == "object", (
        f"window.lwBridge is {surface.get('bridge')!r}, expected 'object'"
    )
    assert surface.get("opsEmitted") == "object", (
        "window.lwBridge does not expose the opsEmitted signal object"
    )
    assert surface.get("opsEmittedConnect") == "function", (
        "window.lwBridge.opsEmitted has no connect() — no envelope can reach "
        "the page"
    )
    assert surface.get("replayFinished") == "object", (
        "window.lwBridge does not expose the replayFinished signal object"
    )
    assert surface.get("replayFinishedConnect") == "function", (
        "window.lwBridge.replayFinished has no connect()"
    )

    # The channel survived the load (strong ref) and the bridge stayed ready.
    assert host._channel is channel
    assert view.bridge.is_ready is True
    _pump(APP, 50)


@pytest.mark.webengine
@needs_webengine
def test_view_cycles_keep_page_loads_alive(app):
    """Q-40: three create/teardown cycles; every cycle's page loads and
    completes the bridge handshake.

    Fails on the pre-Q-40 per-view ownership: after the first teardown the
    profile-global registration dangles (a dead wrapper defeats the
    ``is None`` reinstall guard), so cycle 3+ loads silently never finish —
    the bridge never reports ready and ``lwSnapshot`` is never a function.
    The application-lifetime singleton stays green through all three cycles.
    """
    for cycle in range(3):
        view = LV.LwcChartView()
        try:
            host = view.ensure_host()
            _wait_until(
                app, lambda v=view: v.bridge.is_ready, 30_000,
                f"cycle {cycle}: the page to call bridge.pageReady()",
                host=host, view=view,
            )
            _wait_until(
                app,
                lambda h=host: _run_js(h, "typeof window.lwSnapshot")
                == "function",
                10_000,
                f"cycle {cycle}: chart.js to publish window.lwSnapshot "
                "(pre-Q-40: undefined once the profile registration dangles)",
                host=host, view=view,
            )
        finally:
            _teardown_view(app, view)
