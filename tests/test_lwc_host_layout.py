"""tests/test_lwc_host_layout.py — Q-19/S3a: the host must be laid out.

``ui/lwc_view.py::ensure_host`` built the ``QWebEngineView`` with
``parent=self`` but never added it to a layout, and neither module had a
``resizeEvent``. The host therefore stayed at Qt's default widget size —
measured **100x30 inside a 950x850 view** (``#chart`` clientWidth/clientHeight
100x30) — so even a working transport would have painted a postage stamp.

This module proves the fix structurally and by measurement:

* the view owns a zero-margin, zero-spacing ``QVBoxLayout`` containing the
  host (one change covers the main chart and every pop-out: each LWC view
  creates its own);
* after ``view.resize(950, 850)`` and **no** ``host.resize(...)``, both the
  host widget and the page's ``#chart`` element fill the view (pre-fix they
  measured 100x30).

``@pytest.mark.webengine`` per DG88/AP-P6-4; a skip names its manual
counterpart. The page measurement is a JavaScript answer, not a pixel test, so
it runs under ``QT_QPA_PLATFORM=offscreen``.
"""

from __future__ import annotations

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui import lwc_host as LH  # noqa: E402
from ui import lwc_view as LV  # noqa: E402

LH.register_ndt_scheme()

MANUAL_LAYOUT = (
    "manual: open the app on a Chromium box and confirm the chart canvas "
    "fills the chart area (Q-19 checklist; pre-Q-19 the host measured "
    "100x30 inside a 950x850 view)"
)


def _ensure_app():
    """The session ``QApplication`` with a real ``argv[0]`` (Chromium needs it)."""
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
    reason="no QtWebEngine here — " + MANUAL_LAYOUT,
)


def _pump(app, ms: int) -> None:
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
        try:
            if predicate():
                return
        except RuntimeError:
            pass
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
    from PyQt6.QtCore import QEventLoop, QTimer

    box = {}
    loop = QEventLoop()

    def done(result):
        box["result"] = result
        loop.quit()

    QTimer.singleShot(timeout_ms, loop.quit)
    host.page().runJavaScript(js, 0, done)
    loop.exec()
    assert "result" in box, (
        f"runJavaScript never called back within {timeout_ms} ms"
    )
    return box["result"]


CHART_BOX_JS = """
(function () {
  var el = document.getElementById("chart");
  if (!el) return { w: -1, h: -1 };
  return { w: el.clientWidth, h: el.clientHeight };
})()
"""


def _drain(app, rounds: int = 3) -> None:
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
    """Uninstall the host's profile wiring (Q-15 exit safety)."""
    from PyQt6.QtWebEngineCore import QWebEngineProfile

    try:
        profile = QWebEngineProfile.defaultProfile()
    except Exception:  # pragma: no cover
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
    if view is None:
        return
    host = getattr(view, "_host", None)
    try:
        bridge = view.bridge
    except Exception:  # pragma: no cover
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
                     "pageFocusReleased"):
            signal = getattr(bridge, name, None)
            if signal is None:
                continue
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):
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


@pytest.fixture()
def app():
    if APP is None:  # pragma: no cover
        pytest.skip("no QApplication — QtWebEngine is unavailable here")
    if not APP.arguments():
        pytest.skip(
            "the session QApplication was created with an empty argv; Chromium "
            "aborts on the first profile, so the layout test cannot run in "
            "this process"
        )
    return APP


@pytest.fixture()
def make_view(app):
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
def test_view_owns_a_zero_margin_layout_holding_the_host(app, make_view):
    """Structural half: the host is a laid-out child, not a stray 100x30."""
    from PyQt6.QtWidgets import QVBoxLayout

    view = make_view()
    host = view.ensure_host()

    layout = view.layout()
    assert layout is not None, (
        "LwcChartView has no layout — the host was parented but never laid "
        "out, so it keeps Qt's default size (pre-Q-19: 100x30)"
    )
    assert isinstance(layout, QVBoxLayout)
    margins = layout.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(),
            margins.bottom()) == (0, 0, 0, 0), (
        f"layout margins must be zero, got {margins!r}"
    )
    assert layout.spacing() == 0, f"layout spacing must be zero, got {layout.spacing()}"
    assert layout.indexOf(host) >= 0, "the host is not in the view's layout"
    assert host.parentWidget() is view


@pytest.mark.webengine
@needs_webengine
def test_chart_fills_the_view_without_resizing_the_host(app, make_view):
    """Measured half: 950x850 view -> a 950x850 host and ``#chart`` box.

    No ``host.resize(...)`` anywhere — only the view is resized, exactly as the
    real chart area resizes it.
    """
    view = make_view()
    view.resize(950, 850)
    host = view.ensure_host()

    layout = view.layout()
    assert layout is not None, "no layout: the host cannot follow the view"
    layout.activate()
    # A QWebEngineView's page viewport tracks the widget only once the widget
    # has been shown; no `host.resize(...)` is used anywhere.
    view.show()
    _pump(app, 200)

    assert (host.width(), host.height()) != (100, 30), (
        "the host is still at its default 100x30 — the layout did not give it "
        "the view's geometry"
    )
    assert host.width() >= view.width() - 2, (
        f"host width {host.width()} does not fill the {view.width()} view"
    )
    assert host.height() >= view.height() - 2, (
        f"host height {host.height()} does not fill the {view.height()} view"
    )

    _wait_until(
        app,
        lambda: _run_js(host, "typeof window.lwSnapshot") == "function",
        30_000,
        "the page glue to boot",
    )
    box = _run_js(host, CHART_BOX_JS)
    assert isinstance(box, dict) and box.get("w", -1) > 0, (
        f"#chart was not measurable: {box!r}"
    )
    assert box["w"] >= view.width() - 2, (
        f"#chart clientWidth {box['w']} does not fill the {view.width()} view"
    )
    assert box["h"] >= view.height() - 2, (
        f"#chart clientHeight {box['h']} does not fill the {view.height()} view"
    )
