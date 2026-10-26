"""tests/test_lwc_render_smoke.py — Q-14: the LWC host renders real pixels.

Blank-chart regression, **second cause** (found by rendering the real widget,
not by a test): ``ui/lwc_host.create_host()`` did
``from PyQt6.QtWebEngineWidgets import QWebEngineProfile``. That class lives
in ``PyQt6.QtWebEngineCore``, so every real ``ensure_host()`` raised
``ImportError`` at ``create_host`` time, the host was never constructed and
the chart area stayed black while bars kept loading. Every existing LWC test
missed it because they stub ``ensure_host`` / construct ``LwcHost`` directly.

This module is deliberately *not* a unit test. It drives the real widget:

* ``LwcChartView()`` + ``ensure_host()`` for real (no stub, no monkeypatch);
* a known bar series through ``set_series`` — the ops queue in ``LwBridge``
  until the page signals ready, then the replay crosses (``opsEmitted``);
* the replayed envelope is applied to the **real** page through its own
  documented probe entry point (``window.lwApplyOps``, see chart.js
  ``bindChannel``: "offscreen/probe: ops via lwApplyOps");
* the widget is grabbed to a ``QImage`` and the assertion is pixels, not
  assertions about wiring: the image must not be near-uniform, must differ
  from the pre-data baseline, and must contain the vendored candle colours
  (``#34d399`` up / ``#f87171`` down).

A blank canvas (uniform background) fails all three.

Display requirement (Q-15)
--------------------------
Offscreen Chromium cannot rasterise on this macOS box (SkSurface/RasterDecoder
context lost; measured exit 134 even with ``--disable-gpu --in-process-gpu
--use-gl=swiftshader``) and the surviving page then takes the interpreter down
at exit — "Release of profile requested but WebEnginePage still not deleted",
measured exit 139, which turned a green suite red. The two engine cases
therefore need a **real** display and skip with a named reason everywhere else;
they never "pass" by rendering nothing.

* suite / CI (no display) — engine cases SKIP, the static audit still runs::

      QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \\
          tests/test_lwc_render_smoke.py -q

* developer desktop — the real render and every pixel assertion run (macOS
  ``cocoa``; ``xcb``/``wayland`` on Linux)::

      QT_QPA_PLATFORM=cocoa .venv/bin/python -m pytest \\
          tests/test_lwc_render_smoke.py -m webengine -q -rs

Both engine cases take their view from the ``make_view`` fixture, whose
finaliser stops the page, disconnects the bridge channel, uninstalls the
profile wiring, deletes the page/view and drains deferred deletes — so even a
*failing* render cannot segfault pytest before it reports the failure.

``@pytest.mark.webengine``; the engine cases skip when
``ui.lwc_host.HAS_WEBENGINE`` is False (DG88/AP-P6-4) **or** there is no real
display (Q-15).
"""

from __future__ import annotations

import json
import os
import sys
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from ui import lwc_host as LH  # noqa: E402
from ui import lwc_view as LV  # noqa: E402

# The ``ndt://`` scheme is only honoured when registered before a
# ``QApplication`` exists (Q-13). Module import happens before any test body or
# conftest fixture constructs one, so this is the earliest safe point.
LH.register_ndt_scheme()

#: Ordering probe captured before any QApplication exists. ``create_host``
#: calls ``register_ndt_scheme()`` again later, which overwrites the module
#: global with False (an app exists by then) — the *import-time* value is the
#: one that decides whether ``ndt://`` was registered in time.
REGISTERED_AT_IMPORT = LH.REGISTERED_BEFORE_QAPP


def _ensure_app():
    """The session ``QApplication``, with a program name.

    Chromium (``QWebEngineProfile``) hard-aborts the whole interpreter with
    "Argument list is empty, the program name is not passed to
    QCoreApplication" when the application was built from an empty argv —
    which is what a bare ``QApplication([])`` does. The engine-backed cases
    therefore need the app to exist with a real ``argv[0]``; creating it here,
    at import time, makes this module's app win over any lazily-created one.
    """
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["pytest"])
    return app


try:  # an engine-less box (or a broken display plugin) must not break import
    APP = _ensure_app() if LH.HAS_WEBENGINE else None
except Exception:  # pragma: no cover — QApplication could not be built
    APP = None

#: The documented command that actually renders (see the module docstring).
REAL_DISPLAY_COMMAND = (
    "QT_QPA_PLATFORM=cocoa .venv/bin/python -m pytest "
    "tests/test_lwc_render_smoke.py -m webengine -q -rs "
    "(use xcb/wayland instead of cocoa on Linux)"
)

#: QPA platform plugins that are software stand-ins, not a display. Chromium
#: can start under them but cannot rasterise a ``QWebEngineView`` -- and on
#: this macOS box it then kills the interpreter at exit (Q-15, exit 139).
NO_DISPLAY_PLATFORMS = frozenset({
    "offscreen",
    "minimal",
    "minimalegl",
    "vnc",
    "linuxfb",
    "eglfs",
    "dummy",
})

#: Platform name Qt actually built, or "" when it cannot be asked.
def _active_platform() -> str:
    try:
        from PyQt6.QtGui import QGuiApplication

        return (QGuiApplication.platformName() or "").lower()
    except Exception:  # pragma: no cover — no QtGui at all
        return ""


def _platform_is_headless(name: str) -> bool:
    """True for ``offscreen``/``minimal``/… — a stand-in, not a screen."""
    name = (name or "").strip().lower()
    if not name:
        # An explicit-but-empty QT_QPA_PLATFORM means "let Qt choose".
        return False
    return name.startswith("offscreen") or name in NO_DISPLAY_PLATFORMS


def _display_unavailable_reason() -> str | None:
    """``None`` when a real display can rasterise; otherwise the skip reason.

    Derived from the environment every time it is asked — never a constant —
    so the gate cannot silently decay into "always skip" (Q-15).
    """
    if not LH.HAS_WEBENGINE:
        return (
            "no QtWebEngine here — the real-render proof needs it; manual, on "
            f"a desktop with a display: {REAL_DISPLAY_COMMAND}"
        )
    if APP is None:
        return (
            "no QApplication (the QPA plugin could not start) — manual, on a "
            f"desktop with a display: {REAL_DISPLAY_COMMAND}"
        )
    requested = (os.environ.get("QT_QPA_PLATFORM") or "").strip().lower()
    if _platform_is_headless(requested):
        return (
            f"QT_QPA_PLATFORM={requested}: there is no display to rasterise "
            "the QWebEngineView into, so the real-render proof is skipped "
            "rather than faked; manual, on a desktop with a display: "
            f"{REAL_DISPLAY_COMMAND}"
        )
    platform = _active_platform()
    if _platform_is_headless(platform):
        return (
            f"Qt is running on the {platform or 'unknown'} QPA platform: no "
            "display to rasterise into; manual, on a desktop with a display: "
            f"{REAL_DISPLAY_COMMAND}"
        )
    try:
        screen = APP.primaryScreen()
    except Exception:  # pragma: no cover — screen query failed
        screen = None
    if screen is None:
        return (
            "QApplication reports no screen — manual, on a desktop with a "
            f"display: {REAL_DISPLAY_COMMAND}"
        )
    size = screen.size()
    if size.width() <= 0 or size.height() <= 0:  # pragma: no cover — dummy
        return (
            f"the primary screen reports a {size.width()}x{size.height()} "
            "geometry, so nothing can be rasterised; manual, on a desktop "
            f"with a display: {REAL_DISPLAY_COMMAND}"
        )
    return None


#: ``None`` on a developer desktop, a named reason offscreen/in CI (Q-15).
NO_DISPLAY_REASON = _display_unavailable_reason()

#: Shared gate for the two cases that build a real ``QWebEngineView``.
needs_display = pytest.mark.skipif(
    NO_DISPLAY_REASON is not None,
    reason=NO_DISPLAY_REASON or "",
)

#: Vendored candle colours (chart_assets/lwc/chart.js).
UP_COLOR = (0x34, 0xD3, 0x99)
DOWN_COLOR = (0xF8, 0x71, 0x71)
#: Per-channel tolerance when looking for those colours after compositing.
COLOR_TOLERANCE = 48

#: Sampled-grid step (pixels): keeps QImage scanning cheap but wide.
SAMPLE_STEP = 4
#: A blank chart is one flat background colour; a rendered chart has grid,
#: axis text and candles. Anything at/under this is "near-uniform".
MIN_DISTINCT_COLORS = 24
#: Sampled pixels that must differ from the pre-data baseline.
MIN_CHANGED_SAMPLES = 600
#: Sampled pixels that must carry one of the candle colours.
MIN_CANDLE_SAMPLES = 40

#: Fixed, deterministic series: a rising then falling zig-zag so both candle
#: colours appear (the assertion would pass on a chart that draws only one).
SERIES_TS0 = 1_700_000_000
SERIES_STEP = 60
SERIES_N = 60


def _bars(n: int = SERIES_N):
    """A known bar series with alternating up/down candles."""
    from types import SimpleNamespace

    rows = []
    for i in range(n):
        base = 100.0 + 12.0 * (1 if (i // 6) % 2 == 0 else -1) * (i % 6) / 6.0
        open_ = base
        close = base + (1.5 if i % 2 == 0 else -1.5)
        rows.append(
            SimpleNamespace(
                ts=SERIES_TS0 + i * SERIES_STEP,
                open=open_,
                high=max(open_, close) + 1.0,
                low=min(open_, close) - 1.0,
                close=close,
                volume=1000 + 10 * i,
            )
        )
    return rows


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
    while time.monotonic() < deadline:
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError(f"timed out after {timeout_ms} ms waiting for {what}")


def _grab(host):
    """Grab the real widget to a ``QImage`` (RGB32, ready for pixel reads)."""
    from PyQt6.QtGui import QImage

    pixmap = host.grab()
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB32)
    assert not image.isNull(), "grabbing the LWC host produced a null QImage"
    return image


def _samples(image):
    """Yield ``(x, y, packed_rgb)`` over the sampled grid."""
    for y in range(0, image.height(), SAMPLE_STEP):
        for x in range(0, image.width(), SAMPLE_STEP):
            yield x, y, image.pixel(x, y)


def _rgb(pixel: int):
    return (pixel >> 16) & 0xFF, (pixel >> 8) & 0xFF, pixel & 0xFF


def _is_color(rgb, target) -> bool:
    return all(abs(a - b) <= COLOR_TOLERANCE for a, b in zip(rgb, target))


def _run_js(host, js: str, timeout_ms: int = 5000):
    """Run ``js`` in the loaded page and return its JSON-decoded result."""
    from PyQt6.QtCore import QEventLoop, QTimer

    box = {}
    loop = QEventLoop()

    def done(result):
        box["result"] = result
        loop.quit()

    # Watchdog: a page that died (renderer gone, profile released) never calls
    # back, and a bare ``loop.exec()`` would wedge pytest instead of failing.
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


def _release_profile(view) -> None:
    """Uninstall this view's handlers from the application-owned profile.

    ``ui.lwc_host.create_host`` installs the ``ndt://`` scheme handler and the
    deny-default request interceptor on ``QWebEngineProfile.defaultProfile()``,
    parented to the *view*. The default profile lives as long as the
    QApplication, so it must not be left pointing at objects owned by a widget
    we are about to delete: that dangling wiring is what turns process exit
    into "Release of profile requested but WebEnginePage still not deleted"
    (Q-15). Removing them here makes the profile clean before the page goes;
    the next ``create_host`` installs fresh ones.
    """
    from PyQt6.QtWebEngineCore import QWebEngineProfile

    try:
        profile = QWebEngineProfile.defaultProfile()
    except Exception:  # pragma: no cover — engine already gone
        return
    if profile is None:  # pragma: no cover — no default profile
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
    """Deterministically dismantle a real host (Q-15).

    Runs from the ``make_view`` finaliser, so it executes whether the test
    body passed or failed — a failed render must report, not segfault. Order
    matters: stop the page, disconnect the channel, clean the profile, only
    then delete page and view, and finally drain the deferred deletes.
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
        # 1. Stop the page: no load, paint or JS callback may run once the
        #    test body has returned.
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

    # 2. Disconnect the channel: the bridge's signals are the transport into
    #    this test's Python lists. A queued 33 ms coalesce flush firing after
    #    the frame is gone would write into a dead page.
    if bridge is not None:
        for name in ("opsEmitted", "replayFinished"):
            signal = getattr(bridge, name, None)
            if signal is None:
                continue
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):  # nothing connected / gone
                pass

    # 3. Release the profile wiring while the view still owns its handlers.
    if host is not None:
        _release_profile(view)

    # 4. Delete the widgets and the page. ``host`` is a child of ``view``, and
    #    the view owns its page, so the view's deletion is what actually frees
    #    the QWebEnginePage; the explicit ``page``/``host`` calls cover a page
    #    or host re-parented away from it and are no-ops otherwise (Qt drops
    #    the posted event when the object is already destroyed).
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

    # 5. Drain: deferred deletes only run inside an event-loop iteration.
    _drain(app)


@pytest.fixture()
def app():
    if APP is None:  # pragma: no cover — gated cases skip first
        pytest.skip("no QApplication — QtWebEngine is unavailable here")
    if not APP.arguments():
        pytest.skip(
            "the session QApplication was created with an empty argv; Chromium "
            "aborts on the first profile, so the render smoke test cannot run "
            "in this process"
        )
    return APP


@pytest.fixture()
def make_view(app):
    """Build a real ``LwcChartView`` and guarantee a clean teardown (Q-15)."""
    views = []

    def _make(width: int = 0, height: int = 0):
        view = LV.LwcChartView()
        if width and height:
            view.resize(width, height)
        views.append(view)
        return view

    yield _make
    for view in reversed(views):
        _teardown_view(app, view)


class TestRealHostConstruction:
    """The cause itself: ``ensure_host`` must build a host, not raise."""

    @pytest.mark.webengine
    @needs_display
    def test_ensure_host_constructs_the_real_host(self, app, make_view):
        view = make_view()
        host = view.ensure_host()  # ImportError here on the broken code
        assert isinstance(host, LH.LwcHost)
        assert view.ensure_host() is host, "ensure_host must be lazy, not rebuilt"
        assert REGISTERED_AT_IMPORT is True, (
            "ndt:// was not registered before QApplication — the page cannot "
            "load from the custom scheme in this process"
        )


class TestRealRenderIsNotBlank:
    """The acceptance: pixels, not assertions about wiring."""

    @pytest.mark.webengine
    @needs_display
    def test_end_to_end_render_is_not_near_uniform(self, app, make_view):
        view = make_view(820, 620)

        host = view.ensure_host()  # real construction, no stub
        host.resize(800, 600)
        view.show()
        host.show()

        envelopes = []
        view.bridge.opsEmitted.connect(envelopes.append)

        view.set_series("candles", _bars())

        _wait_until(app, lambda: view.bridge.is_ready, 30_000,
                    "the page to finish loading (bridge ready)")
        _wait_until(app, lambda: envelopes, 10_000,
                    "the bridge to cross the queued series envelope")
        _pump(app, 250)  # first paint of the empty chart

        baseline = _grab(host)
        assert not baseline.isNull()

        envelope = envelopes[-1]
        assert envelope.get("v") == 1 and envelope.get("ops"), (
            f"bridge crossed an unusable envelope: {envelope!r}"
        )
        applied = _run_js(host, "window.lwApplyOps(%s)" % json.dumps(envelope))
        assert isinstance(applied, dict), f"lwApplyOps returned {applied!r}"
        assert applied.get("error") is None, (
            f"the page rejected the envelope: {applied.get('error')!r}"
        )
        assert applied.get("applied") == len(envelope["ops"]), (
            f"page applied {applied.get('applied')} of "
            f"{len(envelope['ops'])} ops — the render surface is not fed"
        )

        _pump(app, 600)  # let lightweight-charts paint the series

        image = _grab(host)
        assert image.width() >= 400 and image.height() >= 300, (
            f"host grabbed at {image.width()}x{image.height()} — too small to "
            "prove anything about the chart canvas"
        )

        colors = set()
        changed = 0
        candle_pixels = 0
        for x, y, pixel in _samples(image):
            colors.add(pixel)
            if pixel != baseline.pixel(x, y):
                changed += 1
            rgb = _rgb(pixel)
            if _is_color(rgb, UP_COLOR) or _is_color(rgb, DOWN_COLOR):
                candle_pixels += 1

        # 1. Not near-uniform: a blank (single-colour) canvas fails here.
        assert len(colors) > MIN_DISTINCT_COLORS, (
            "the grabbed chart is near-uniform: only "
            f"{len(colors)} distinct sampled colours (a blank canvas is 1). "
            "The LWC host rendered nothing."
        )
        # 2. The bars actually landed: the image changed where the data went.
        assert changed > MIN_CHANGED_SAMPLES, (
            "the chart image is identical to the pre-data baseline: "
            f"{changed} sampled pixels changed (need >{MIN_CHANGED_SAMPLES}). "
            "The series never reached the page."
        )
        # 3. Candle colours are on screen, both directions of the zig-zag.
        assert candle_pixels >= MIN_CANDLE_SAMPLES, (
            "no candle body pixels in the grabbed image: "
            f"{candle_pixels} sampled pixels near #34d399/#f87171 "
            f"(need >={MIN_CANDLE_SAMPLES})"
        )


class TestDisplayGate:
    """Q-15: the gate is derived from the environment, never hardwired.

    A smoke test that skips on a developer desktop as well would be worthless,
    so this pins both directions: a headless QPA platform must produce a named
    reason, and on a real display the gate must be open.
    """

    def test_headless_qpa_platforms_are_named(self):
        for name in ("offscreen", "offscreen:nowindow", "minimal",
                     "minimalegl", "vnc", "linuxfb"):
            assert _platform_is_headless(name), (
                f"{name!r} is a software stand-in, not a display"
            )

    def test_real_qpa_platforms_are_not_headless(self):
        for name in ("cocoa", "windows", "xcb", "wayland", ""):
            assert not _platform_is_headless(name), (
                f"{name!r} is a real display path (or 'let Qt choose')"
            )

    def test_the_gate_matches_the_display_it_is_running_on(self):
        platform = _active_platform() or (os.environ.get("QT_QPA_PLATFORM") or "")
        no_display = (
            not LH.HAS_WEBENGINE
            or APP is None
            or _platform_is_headless(platform)
        )
        if no_display:
            assert NO_DISPLAY_REASON, (
                "there is no display here, so the engine cases must skip with "
                "a named reason instead of starting Chromium"
            )
        else:
            assert NO_DISPLAY_REASON is None, (
                "this session has a real display but the render smoke test is "
                f"gated off ({NO_DISPLAY_REASON!r}) — it must not become a "
                "test that always skips"
            )


#: Ownership table (verified against PyQt6 6.11.0): Core owns every engine
#: class this module uses except the view itself.
CORE_OWNED = {
    "QWebEngineProfile",
    "QWebEngineSettings",
    "QWebEnginePage",
    "QWebEngineScript",
    "QWebEngineUrlScheme",
    "QWebEngineUrlSchemeHandler",
    "QWebEngineUrlRequestInterceptor",
}
WIDGETS_OWNED = {"QWebEngineView"}


class TestEngineImportAudit:
    """Q-14: no engine class may be imported from the wrong Qt module.

    Runs without an engine (static AST scan) so a wrong ``from`` cannot hide
    behind a ``HAS_WEBENGINE`` skip: the broken code imported a Core class
    from Widgets and the guard stayed green because every test stubbed the
    host.
    """

    def test_no_engine_class_imported_from_the_wrong_module(self):
        import ast
        from pathlib import Path

        source = (Path(__file__).resolve().parent.parent / "ui" / "lwc_host.py"
                  ).read_text(encoding="utf-8")
        offenders = []
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if not module.startswith("PyQt6.QtWebEngine"):
                continue
            owner = module.rsplit(".", 1)[-1]
            for alias in node.names:
                name = alias.name
                if name in CORE_OWNED and owner != "QtWebEngineCore":
                    offenders.append(f"{name} imported from {module}")
                elif name in WIDGETS_OWNED and owner != "QtWebEngineWidgets":
                    offenders.append(f"{name} imported from {module}")
        assert not offenders, (
            "engine class imported from the wrong Qt module (ImportError at "
            "host construction, swallowed by ensure_host -> blank chart): "
            + "; ".join(offenders)
        )

    def test_ownership_proven_by_real_imports(self):
        """The table above is a fact about the installed PyQt6, not a guess."""
        from PyQt6 import QtWebEngineCore
        from PyQt6 import QtWebEngineWidgets

        if not LH.HAS_WEBENGINE:
            pytest.skip(
                "PyQt6-QtWebEngine is not installed here — the static audit "
                "above still runs; the runtime ownership proof needs it"
            )
        for name in sorted(CORE_OWNED):
            assert hasattr(QtWebEngineCore, name), (
                f"{name} is not in PyQt6.QtWebEngineCore"
            )
            assert not hasattr(QtWebEngineWidgets, name), (
                f"{name} unexpectedly exists in PyQt6.QtWebEngineWidgets"
            )
        assert hasattr(QtWebEngineWidgets, "QWebEngineView")
        assert not hasattr(QtWebEngineCore, "QWebEngineView"), (
            "QWebEngineView belongs to QtWebEngineWidgets"
        )

