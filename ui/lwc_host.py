"""ui/lwc_host.py — offline LWC host (P6-04, D47.3).

A ``QWebEngineView`` serving the vendored lightweight-charts v5.2.x tree
through a custom ``ndt://`` scheme:

* the scheme handler is registered **before** ``QApplication`` exists
  (``register_ndt_scheme()`` records the ordering probe
  ``REGISTERED_BEFORE_QAPP``);
* ``ndt://lwc/`` resolves into ``chart_assets/lwc/`` (version pin asserted);
* the request interceptor is **deny-default** — only ``ndt`` (+ the Qt
  ``qrc`` webchannel shim and ``data``/``blob`` subresources) is allowed, so
  a non-``ndt`` (``https:``/``http:``) request is blocked and the airplane
  case stays green with no network;
* the ``QWebChannel`` is created, ``lwBridge`` is registered on it and the
  channel is attached with ``QWebEnginePage.setWebChannel`` **before** the
  page load (Q-16). Qt only injects ``qt.webChannelTransport`` into a page
  that already had a channel when the load started; attaching afterwards
  leaves ``qt`` undefined and ``window.lwBridge`` forever absent. The host
  keeps a strong reference (``self._channel``) and re-attaches the channel
  before every reload, so a renderer restart keeps the handshake;
* attribution for the vendored tree ships in
  ``chart_assets/lwc/ATTRIBUTION.md`` and is exposed via
  ``attribution_text()``.

Focus/keyboard model (named in-code per DG92): ``FOCUS_KEYBOARD_MODEL``
(``lwc-focus-forward-v1``) — the chart wrapper is tab-focusable, Arrow keys
pan, ``+``/``-`` zoom, and Esc releases focus back to the Qt focus chain via
``LwcHost.focusReleased``.

Renderer boundary: this module serves static assets and forwards bridge ops
only. No broker surface, no DB/store, no service, no symbol-list/layout
surface and no order surface is touched here.

Everything engine-specific is import-guarded (``HAS_WEBENGINE``): offscreen
CI without Chromium imports this module fine and the engine-gated cases skip
(never red) per DG88/AP-P6-4.
"""

from __future__ import annotations

import logging
import mimetypes
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit

_LOG = logging.getLogger(__name__)

#: Custom scheme hosting the vendored tree: ``ndt://lwc/<asset>``.
NDT_SCHEME = "ndt"
#: Host served by the scheme handler.
NDT_HOST = "lwc"

#: Pinned vendored lightweight-charts version (v5.2.x tree). Must equal
#: ``chart_assets/lwc/VERSION`` and the vendored header — asserted by
#: ``tests/test_lwc_bridge.py::P6-T04-T11``.
LWC_PINNED_VERSION = "5.2.1"

#: DG92 focus/keyboard model, named in-code.
FOCUS_KEYBOARD_MODEL = (
    "lwc-focus-forward-v1: the chart wrapper is tab-focusable inside the "
    "QWebEngineView; Arrow keys pan, +/- zoom, Esc releases focus back to "
    "the Qt focus chain (focusReleased)."
)

#: Schemes the deny-default interceptor lets through. ``qrc`` carries only
#: the Qt-provided webchannel shim; ``data``/``blob`` cover canvas-local
#: subresources. Everything else — including ``https:``/``http:``/``file:``
#: and unknown schemes — is blocked.
ALLOWED_SCHEMES = ("ndt", "qrc", "data", "blob")

#: Ordering probe: result of the last ``register_ndt_scheme()`` call — True
#: when no ``QApplication`` existed yet (the required order), False/None
#: otherwise. ``None`` until the first call.
REGISTERED_BEFORE_QAPP: bool | None = None

#: ESC-071: bound on the recent page-console messages the host keeps. The
#: browser also prints them; this deque is what lets an offscreen test assert
#: that a page-level error was actually seen (never an unbounded log).
JS_CONSOLE_HISTORY = 50

#: Qt's ``QWebEnginePage.JavaScriptConsoleMessageLevel`` values, named.
JS_CONSOLE_LEVELS = {
    0: "INFO",
    1: "WARNING",
    2: "ERROR",
}

#: ``QWebChannel`` object name the page's JS looks up
#: (``chart_assets/lwc/chart.js::bindChannel`` does
#: ``channel.objects.lwBridge``). The Python registration and the JS lookup
#: must stay the same string (Q-16).
BRIDGE_OBJECT_NAME = "lwBridge"

ASSET_DIR = Path(__file__).resolve().parent.parent / "chart_assets" / "lwc"
ATTRIBUTION_FILE = ASSET_DIR / "ATTRIBUTION.md"
VERSION_FILE = ASSET_DIR / "VERSION"


def is_request_allowed(url: str) -> bool:
    """Deny-default URL classifier: True only for ``ALLOWED_SCHEMES``.

    Pure function (no engine needed) so the interceptor cases run green on
    engine-less CI; the wired interceptor delegates to exactly this.
    """
    try:
        scheme = urlsplit(str(url)).scheme.lower()
    except Exception:
        return False
    return scheme in ALLOWED_SCHEMES


def asset_path_for_url(url: str):
    """Map an ``ndt://lwc/<rel>`` URL to a file under ``ASSET_DIR``.

    Returns ``None`` for foreign hosts, absolute paths, or ``..`` escapes.
    """
    try:
        parts = urlsplit(str(url))
    except Exception:
        return None
    if parts.scheme.lower() != NDT_SCHEME or parts.hostname != NDT_HOST:
        return None
    rel = (parts.path or "/").lstrip("/")
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return None
    candidate = ASSET_DIR / rel
    if candidate.is_dir():
        candidate = candidate / "chart.html"
    return candidate


def lwc_version() -> str:
    """Read the vendored-tree version declaration (``VERSION`` file)."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def attribution_text() -> str:
    """Return the vendored-tree attribution document (AC-D47.3)."""
    return ATTRIBUTION_FILE.read_text(encoding="utf-8")


def register_ndt_scheme() -> bool:
    """Register the ``ndt`` scheme; must run before ``QApplication`` exists.

    Returns (and records in ``REGISTERED_BEFORE_QAPP``) whether no
    ``QApplication`` instance existed at call time — the required order.
    Safe to call without an engine installed: scheme registration is then
    skipped but the ordering probe is still recorded.
    """
    global REGISTERED_BEFORE_QAPP
    try:
        from PyQt6.QtWidgets import QApplication
        before = QApplication.instance() is None
    except Exception:
        before = True
    REGISTERED_BEFORE_QAPP = before
    if not _HAS_WEBENGINE or not before:
        return bool(before)
    from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
    scheme = QWebEngineUrlScheme(NDT_SCHEME.encode())
    scheme.setSyntax(QWebEngineUrlScheme.Syntax.Host)
    scheme.setFlags(
        QWebEngineUrlScheme.Flag.LocalScheme
        | QWebEngineUrlScheme.Flag.LocalAccessAllowed
        | QWebEngineUrlScheme.Flag.SecureScheme
        | QWebEngineUrlScheme.Flag.CorsEnabled
    )
    QWebEngineUrlScheme.registerScheme(scheme)
    return True


# Engine symbol ownership (Q-14: a blank chart hid behind getting this wrong).
# ``PyQt6.QtWebEngineCore`` owns QWebEngineUrlScheme,
# QWebEngineUrlSchemeHandler, QWebEngineUrlRequestInterceptor,
# QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineScript.
# ``PyQt6.QtWebEngineWidgets`` owns exactly QWebEngineView.
# Importing a Core class from the Widgets module raises ImportError at host
# construction time — inside ``ensure_host``, where callers swallow it — so
# the chart stays black with no test failure. Keep every import here on its
# owning module; ``tests/test_lwc_render_smoke.py`` audits this statically.
try:  # pragma: no cover — exercised on engine boxes, skipped elsewhere
    from PyQt6.QtCore import QBuffer, QIODevice, QByteArray  # noqa: F401
    from PyQt6.QtWebEngineCore import (
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineUrlSchemeHandler,
        QWebEngineUrlRequestInterceptor,
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    # Q-16: the page transport. Owned by ``PyQt6.QtWebChannel`` (it ships
    # with QtWebEngine); imported with the engine guard so an engine-less
    # box still imports this module (DG88/AP-P6-4).
    from PyQt6.QtWebChannel import QWebChannel

    _HAS_WEBENGINE = True
except Exception:  # offscreen CI without Chromium (DG88): import-safe
    _HAS_WEBENGINE = False

HAS_WEBENGINE = _HAS_WEBENGINE

if HAS_WEBENGINE:  # pragma: no cover — engine-only surface

    class NdtSchemeHandler(QWebEngineUrlSchemeHandler):
        """Serve ``ndt://lwc/*`` from the vendored ``chart_assets/lwc/`` tree."""

        def requestStarted(self, job) -> None:  # noqa: N802 (Qt naming)
            target = asset_path_for_url(job.requestUrl().toString())
            if target is None or not target.is_file():
                job.fail(job.Error.RequestDenied)
                return
            try:
                data = target.read_bytes()
            except OSError:
                job.fail(job.Error.RequestFailed)
                return
            mime, _ = mimetypes.guess_type(target.name)
            buf = QBuffer(job)
            buf.setData(QByteArray(data))
            buf.open(QIODevice.OpenModeFlag.ReadOnly)
            job.reply((mime or "application/octet-stream").encode(), buf)

    class LwcRequestInterceptor(QWebEngineUrlRequestInterceptor):
        """Deny-default: block everything ``is_request_allowed`` rejects."""

        def interceptRequest(self, info) -> None:  # noqa: N802 (Qt naming)
            if not is_request_allowed(info.requestUrl().toString()):
                info.block(True)

    class NdtWebPage(QWebEnginePage):
        """Page that makes JavaScript console output VISIBLE (ESC-071).

        ``QWebEnginePage``'s default ``javaScriptConsoleMessage`` sends page
        errors (``qt is not defined``, ``addCandlestickSeries is not a
        function``) only to stderr, so a renderer failure left no trace in the
        application log. Every message is forwarded to logging at WARNING with
        its level, source and line, and the most recent ones are retained in a
        bounded deque so an offscreen test can assert what the page reported.
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.console_messages = deque(maxlen=JS_CONSOLE_HISTORY)

        def javaScriptConsoleMessage(  # noqa: N802 (Qt naming)
            self, level, message, line_number, source_id
        ) -> None:
            raw_level = getattr(level, "value", level)
            name = JS_CONSOLE_LEVELS.get(raw_level, str(raw_level))
            text = str(message)
            self.console_messages.append({
                "level": name,
                "message": text,
                "line": int(line_number),
                "source": str(source_id),
            })
            _LOG.warning(
                "JavaScript console [%s] %s (%s:%s)",
                name, text, source_id, line_number,
            )

    from PyQt6.QtCore import pyqtSignal as _sig
    from PyQt6.QtWidgets import QSizePolicy as _SP

    class LwcHost(QWebEngineView):
        """Offline ``QWebEngineView`` host for the vendored LWC tree.

        Focus/keyboard model: ``FOCUS_KEYBOARD_MODEL``
        (``lwc-focus-forward-v1``, DG92).
        """

        focusReleased = _sig()

        def __init__(self, bridge, parent=None):
            super().__init__(parent)
            self._bridge = bridge
            # ESC-071: install the console-capturing page before anything can
            # load or attach a channel. ``setPage`` retires the page the view
            # created in ``super().__init__`` itself; the custom page is kept
            # referenced (``setPage`` does not take ownership).
            self._console_page = NdtWebPage(self)
            self.setPage(self._console_page)
            # Q-16: the channel must exist and be attached to the page BEFORE
            # the first ``load``. Qt injects ``qt.webChannelTransport`` only
            # for a page that already had a channel when the load began, and
            # the JS half (``chart.js::bindChannel``) needs it to publish
            # ``channel.objects.lwBridge``. The strong reference keeps the
            # QWebChannel alive for the page's lifetime (``setWebChannel``
            # does not take ownership).
            self._channel = None
            self._attach_web_channel()
            self.setFocusPolicy(self.focusPolicy().__class__.StrongFocus)
            self.setSizePolicy(_SP.Policy.Expanding, _SP.Policy.Expanding)
            self.renderProcessTerminated.connect(self._on_render_terminated)
            self.loadFinished.connect(self._on_load_finished)

        def _attach_web_channel(self):
            """Register ``lwBridge`` and attach the channel to the page.

            Idempotent: the first call creates the ``QWebChannel`` and
            registers the bridge under ``BRIDGE_OBJECT_NAME``; every later
            call re-applies the same channel to the page (the re-load path
            after ``renderProcessTerminated``). Must run before ``load`` —
            see the constructor note (Q-16).
            """
            page = self.page()
            channel = self._channel
            if channel is None:
                channel = QWebChannel(self)
                self._channel = channel
                channel.registerObject(BRIDGE_OBJECT_NAME, self._bridge)
            page.setWebChannel(channel)
            return channel

        def host_url(self) -> str:
            return f"{NDT_SCHEME}://{NDT_HOST}/chart.html"

        def load_chart(self) -> None:
            from PyQt6.QtCore import QUrl

            # Re-attach first: a reload after a renderer restart gets the
            # channel (and its injected transport) exactly as the first load
            # did. Attaching after ``load`` would be too late (Q-16).
            self._attach_web_channel()
            self.load(QUrl(self.host_url()))

        def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt naming)
            from PyQt6.QtCore import Qt

            if event.key() == Qt.Key.Key_Escape:
                self.focusReleased.emit()
                event.accept()
                return
            super().keyPressEvent(event)

        def _on_render_terminated(self, *args) -> None:
            self._bridge.handle_render_terminated()
            # The page object (and with it ``self._channel``) survives the
            # renderer process; ``load_chart`` re-attaches the channel before
            # reloading, so the fresh page gets ``qt.webChannelTransport`` and
            # the bridge handshake again (Q-16).
            self.load_chart()  # reload into a fresh renderer

        def _on_load_finished(self, ok: bool) -> None:
            if ok:
                self._bridge.handle_page_ready()

    def create_host(bridge, parent=None):
        """Register the scheme/profile wiring and return an ``LwcHost``."""
        register_ndt_scheme()
        profile = QWebEngineProfile.defaultProfile()
        if profile.urlSchemeHandler(NDT_SCHEME.encode()) is None:
            profile.installUrlSchemeHandler(
                NDT_SCHEME.encode(), NdtSchemeHandler(parent)
            )
        interceptor = LwcRequestInterceptor(parent)
        profile.setUrlRequestInterceptor(interceptor)
        host = LwcHost(bridge, parent)
        host.load_chart()
        return host

else:

    def create_host(bridge, parent=None):  # type: ignore[misc]
        """Engine-less stub: raises; engine boxes never reach this branch."""
        raise RuntimeError(
            "QtWebEngine is not available — LwcHost cannot be created "
            "(offscreen CI without Chromium; see DG88)."
        )
