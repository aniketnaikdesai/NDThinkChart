"""tests/test_lwc_failure_visibility.py — Q-18: failure must be VISIBLE.

Four review findings with one theme: a chart that cannot start, a page whose
JavaScript throws, or a residue scan that forbids a word must not fail
silently.

* ESC-070 — ``ensure_host()`` raising is logged with a full traceback, sets
  ``MainWindow.chart_engine_failed`` and posts a status-bar message naming the
  engine; the success path stays quiet.
* ESC-071 — page-level JavaScript console output is captured on the host's own
  page and forwarded to logging at WARNING. An offscreen ``runJavaScript``
  throw is the proof (no rasterisation needed).
* ESC-072 — the five renderer residue scans assert the *property* (no
  pyqtgraph import/instantiation) rather than the literal word, so a docstring
  mention passes while an import still fails.
* ESC-073 — every archived result attributes itself by ``task_id``.

QApplication: the JS-console case needs a real QtWebEngine page. Like the Q-16
handshake suite, the application is created at import time with a non-empty
argv (Chromium aborts on an empty one); an engine-less box skips, never fails.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PyQt6.QtWidgets import QWidget  # noqa: E402

from ui import lwc_host as LH  # noqa: E402
from ui import lwc_view as LV  # noqa: E402

# The ``ndt://`` scheme is honoured only when registered before a
# ``QApplication`` exists (Q-13). This module may be imported before the Q-16
# handshake suite (it is first in the Q-18 test command) and creates the app
# below, so it registers the scheme first, at the earliest safe point.
LH.register_ndt_scheme()

REPO = Path(__file__).resolve().parent.parent
ARCHIVE = REPO / "docs" / "build" / "results" / "_archive"

MANUAL_JS_CONSOLE = (
    "manual: open the app on a Chromium box and confirm a page error appears "
    "in the application log at WARNING (Q-18 checklist)"
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
    reason="no QtWebEngine here — " + MANUAL_JS_CONSOLE,
)


# ── ESC-070 · silent engine failure ─────────────────────────────────────────


class _FailingPanel(QWidget):
    """A chart view whose engine host cannot start (engine-less CI)."""

    ENGINE_NAME = "lwc"

    def ensure_host(self):
        raise RuntimeError("ESC-070 probe: QtWebEngine is unavailable")


class _HealthyPanel(QWidget):
    """A chart view whose engine host starts normally."""

    ENGINE_NAME = "lwc"

    def __init__(self):
        super().__init__()
        self.host = object()

    def ensure_host(self):
        return self.host


def _make_window(monkeypatch, panel):
    """Construct a real ``MainWindow`` with a controlled chart panel."""
    from ibkr.client import IBApiClient
    import ui.main_window as main_window

    monkeypatch.setattr(IBApiClient, "connect", lambda *a, **k: None)
    monkeypatch.setattr(IBApiClient, "run", lambda *a, **k: None)
    monkeypatch.setattr(
        main_window, "build_main_chart_view", lambda **kwargs: panel)
    return main_window.MainWindow()


def test_engine_failure_is_logged_flagged_and_shown(qapp, monkeypatch, caplog):
    from ui.main_window import chart_engine_failure_message

    panel = _FailingPanel()
    caplog.set_level(logging.ERROR, logger="ui.main_window")
    win = _make_window(monkeypatch, panel)
    try:
        qapp.processEvents()

        # (b) the explicit attribute distinguishes "failed" from "empty".
        assert win.chart_engine_failed is True
        assert win._chart_engine_host is None

        # (c) the user sees which engine failed and that the chart is blank.
        assert win.status_bar.currentMessage() == (
            chart_engine_failure_message("lwc"))
        assert "lwc" in win.status_bar.currentMessage()

        # (a) the exception is in the log at ERROR with its traceback.
        errors = [
            record for record in caplog.records
            if record.name == "ui.main_window"
            and record.levelno == logging.ERROR
        ]
        assert errors, "the engine failure was not logged at ERROR"
        assert any("could not start" in record.getMessage()
                   for record in errors)
        assert all(record.exc_info is not None for record in errors), (
            "the log record carries no traceback")
        assert "ESC-070 probe" in caplog.text
    finally:
        win.close()
        qapp.processEvents()


def test_engine_success_is_quiet(qapp, monkeypatch, caplog):
    panel = _HealthyPanel()
    caplog.set_level(logging.ERROR, logger="ui.main_window")
    win = _make_window(monkeypatch, panel)
    try:
        assert win.chart_engine_failed is False
        assert win._chart_engine_host is panel.host
        assert win.status_bar.currentMessage() == "Connecting to IBKR…"
        assert "could not start" not in win.status_bar.currentMessage().lower()
        assert [
            record for record in caplog.records
            if record.name == "ui.main_window"
            and record.levelno >= logging.ERROR
        ] == []
    finally:
        win.close()
        qapp.processEvents()


# ── ESC-071 · JavaScript console capture ────────────────────────────────────


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


def _drain(app, rounds: int = 3) -> None:
    """Run the loop and flush deferred deletes (``deleteLater`` needs this)."""
    from PyQt6.QtCore import QCoreApplication, QEvent, QEventLoop

    for _ in range(rounds):
        try:
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
            QCoreApplication.sendPostedEvents(
                None, int(QEvent.Type.DeferredDelete))
            app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 50)
        except Exception:  # pragma: no cover — teardown must never raise
            return


def _teardown_host(app, host, view) -> None:
    for call in (getattr(host, "stop", None), getattr(host, "hide", None)):
        if call is not None:
            try:
                call()
            except Exception:  # pragma: no cover
                pass
    try:
        view.hide()
    except Exception:  # pragma: no cover
        pass
    try:
        host.deleteLater()
    except Exception:  # pragma: no cover
        pass
    try:
        view.deleteLater()
    except Exception:  # pragma: no cover
        pass
    _drain(app)


@pytest.fixture()
def app():
    if APP is None:  # pragma: no cover — the gated case skips first
        pytest.skip("no QApplication — QtWebEngine is unavailable here")
    if not APP.arguments():
        pytest.skip(
            "the session QApplication was created with an empty argv; Chromium "
            "aborts on the first profile, so the JS-console test cannot run "
            "in this process"
        )
    return APP


@pytest.mark.webengine
@needs_webengine
def test_js_console_errors_are_captured_and_logged(app, caplog):
    view = LV.LwcChartView()
    host = LH.LwcHost(view.bridge)
    try:
        page = host.page()
        assert isinstance(page, LH.NdtWebPage), (
            "the host must install the console-capturing page on itself; "
            "otherwise page errors reach only stderr")

        caplog.set_level(logging.WARNING, logger="ui.lwc_host")
        page.runJavaScript(
            "(function () { throw new Error('ESC-071 probe'); })();")
        _wait_until(
            app,
            lambda: any("ESC-071 probe" in entry["message"]
                        for entry in page.console_messages),
            10_000,
            "the thrown JS error to reach javaScriptConsoleMessage",
        )

        captured = [entry for entry in page.console_messages
                    if "ESC-071 probe" in entry["message"]]
        assert captured, "the page console hook captured nothing"
        assert captured[-1]["level"] == "ERROR"
        assert isinstance(captured[-1]["source"], str)
        assert isinstance(captured[-1]["line"], int)
        assert len(page.console_messages) <= LH.JS_CONSOLE_HISTORY

        records = [
            record for record in caplog.records
            if record.name == "ui.lwc_host"
            and "ESC-071 probe" in record.getMessage()
        ]
        assert records, "the JS console message never reached the log"
        assert records[-1].levelno == logging.WARNING
        assert "ERROR" in records[-1].getMessage()
        _pump(app, 50)
    finally:
        _teardown_host(app, host, view)


# ── ESC-072 · residue scans assert the property, not the word ──────────────

SCAN_MODULES = (
    "test_lwc_time_parity.py",
    "test_lwc_studies.py",
    "test_lwc_alarms.py",
    "test_lwc_drawings.py",
    "test_lwc_overlays.py",
)


def _load_scan_module(filename: str):
    path = REPO / "tests" / filename
    spec = importlib.util.spec_from_file_location(f"q18_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("filename", SCAN_MODULES)
def test_renderer_scan_asserts_the_property_not_the_word(filename):
    module = _load_scan_module(filename)
    uses = getattr(module, "_uses_pyqtgraph")

    # Documentation may name the default engine (P6-T11 was forced to rewrite
    # a docstring); code may not import or instantiate it.
    assert uses('"""The default engine is pyqtgraph."""\nVALUE = 1\n') is False
    assert uses("# pyqtgraph is the default engine\nVALUE = 1\n") is False
    for violation in (
        "import pyqtgraph\n",
        "from pyqtgraph import PlotWidget\n",
        "import pyqtgraph as pg\n",
        "PLOT = pyqtgraph.PlotWidget()\n",
    ):
        assert uses(violation) is True, violation


def test_lwc_view_does_not_import_or_use_pyqtgraph():
    module = _load_scan_module("test_lwc_time_parity.py")
    source = (REPO / "ui" / "lwc_view.py").read_text(encoding="utf-8")
    assert module._uses_pyqtgraph(source) is False


# ── ESC-073 · archived results attribute themselves ────────────────────────


_ARCHIVE_NAME = re.compile(r"^wave(\d+)_(.+)\.json$")


def _archive_wave_and_stem(filename: str):
    """Split an archive filename into ``(wave number, task stem)``.

    The stem is the token after the wave prefix, e.g. ``P8-T02`` in
    ``wave163_P8-T02.json``; a dotted suffix such as ``.PRIOR_PHASE`` or
    ``.ORPHAN`` belongs to the wave record, not the task. Names outside
    the convention return ``(None, filename)`` and sort oldest.
    """
    match = _ARCHIVE_NAME.match(filename)
    if match is None:
        return (None, filename)
    return (int(match.group(1)), match.group(2).split(".")[0])


def _newest_per_task(entries):
    """Group archive entries by task stem, keeping the newest wave per task.

    ``entries`` is an iterable of mappings with at least ``name`` (the
    archive filename); any other keys (e.g. ``task_id``) ride along
    untouched. Pure — no disk access — so unit-testable on synthetic dicts.
    """
    newest: dict = {}
    for entry in entries:
        wave, stem = _archive_wave_and_stem(entry["name"])
        order = wave if wave is not None else -1
        current = newest.get(stem)
        if current is None or order > current[0]:
            newest[stem] = (order, entry)
    return {stem: entry for stem, (_, entry) in newest.items()}


def _newest_missing_task_id(entries):
    """Names of newest-per-task entries carrying no ``task_id`` (fail-closed)."""
    return sorted(
        entry["name"]
        for entry in _newest_per_task(entries).values()
        if not entry.get("task_id")
    )


def test_archived_results_carry_task_id():
    entries = []
    for path in sorted(ARCHIVE.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries.append({"name": path.name, "task_id": data.get("task_id")})
    # Only the newest file per task stem must attribute itself: superseded
    # intermediates (older same-task waves) can never redden this gate,
    # while a newest result missing task_id still fails it.
    missing = _newest_missing_task_id(entries)
    assert missing == [], f"archived results without task_id: {missing}"

    wave127 = json.loads(
        (ARCHIVE / "wave127_P6-T03.json").read_text(encoding="utf-8"))
    assert wave127["task_id"] == "P6-T03"


def test_newest_per_task_helper_flags_missing_task_id():
    """The grouping helper is fail-closed on synthetic dicts (no disk write)."""
    entries = [
        {"name": "wave156_P8-T02.json", "task_id": ""},
        {"name": "wave163_P8-T02.json", "task_id": "P8-T02"},
        {"name": "wave159_P8-T03.json", "task_id": None},
        {"name": "wave163_P8-T03.json", "task_id": "P8-T03"},
        {"name": "wave160_P8-T05.json", "task_id": ""},
    ]
    newest = _newest_per_task(entries)
    assert {entry["name"] for entry in newest.values()} == {
        "wave163_P8-T02.json", "wave163_P8-T03.json", "wave160_P8-T05.json",
    }
    # The superseded intermediates without task_id are excluded, while the
    # newest result without task_id is still reported missing.
    assert _newest_missing_task_id(entries) == ["wave160_P8-T05.json"]
