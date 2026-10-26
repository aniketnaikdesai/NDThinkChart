"""tests/test_lwc_host_bootstrap.py — Q-13: ndt:// is registered before QApplication.

Blank-chart regression: ``main.py`` never called
``ui.lwc_host.register_ndt_scheme()``, and ``ui/lwc_host`` was only imported
lazily from the engine factory — after ``QApplication`` was constructed. At
that point the ``QtWebEngine`` import fails (Qt requires it before
``QApplication``), so ``HAS_WEBENGINE`` is False, ``LwcChartView.ensure_host()``
raises, the exception is swallowed, and the chart area stays black while bars
keep loading (status bar "… Stream live.").

Two cases pin the fix:

* a static AST ordering assertion — the registration call sits at module level
  in ``main.py``, above the ``QApplication(...)`` call, so a refactor that
  moves it is caught;
* a subprocess probe — import ``main``, construct ``QApplication``, then check
  ``ui.lwc_host.HAS_WEBENGINE`` is True (offscreen, no display, no TWS).
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = ROOT / "main.py"

#: Names that count as "register the ndt:// scheme" in main.py. The helper is
#: preferred; a direct ``register_ndt_scheme`` call is accepted too.
REGISTRATION_CALLS = {"_register_lwc_scheme_before_qapp", "register_ndt_scheme"}


def _main_tree() -> ast.Module:
    return ast.parse(MAIN_PY.read_text(encoding="utf-8"))


def _called_name(node: ast.Call):
    """Name of a call target: ``f()`` -> 'f', ``mod.f()`` -> 'f'."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _all_call_lines(tree: ast.Module, names: set[str]) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _called_name(node) in names
    ]


def _module_level_call_lines(tree: ast.Module, names: set[str]) -> list[int]:
    """Lines of matching calls that actually run at import time.

    Top-level statements other than ``def``/``class`` run on import, so calls
    nested in an ``if``/``try`` there count. Calls inside a function body do
    not — importing the module would never reach them.
    """
    lines: list[int] = []
    for statement in tree.body:
        if isinstance(
            statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and _called_name(node) in names:
                lines.append(node.lineno)
    return lines


class TestSchemeRegistrationOrdering:
    """Static guard: registration runs at module import, before QApplication."""

    def test_registration_runs_at_module_import(self):
        module_lines = _module_level_call_lines(_main_tree(), REGISTRATION_CALLS)
        assert module_lines, (
            "main.py must call the ndt:// scheme registration at module level "
            "(import time). A call buried in a function runs after "
            "QApplication and leaves the LWC chart blank."
        )

    def test_registration_precedes_qapplication(self):
        tree = _main_tree()
        module_lines = _module_level_call_lines(tree, REGISTRATION_CALLS)
        app_lines = _all_call_lines(tree, {"QApplication"})
        assert app_lines, "main.py no longer constructs QApplication"
        assert min(module_lines) < min(app_lines), (
            f"scheme registration (line {min(module_lines)}) must come before "
            f"QApplication (line {min(app_lines)}): QtWebEngine only honours "
            "QWebEngineUrlScheme.registerScheme() when no QApplication exists"
        )

#: Child-process script: main's module import must register the scheme (and
#: pull in QtWebEngine) before we construct QApplication.
_PROBE = r"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import main  # noqa: F401  — module import registers ndt:// before QApplication

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

import ui.lwc_host as host

assert host.HAS_WEBENGINE is True, (
    "QtWebEngine was imported too late (HAS_WEBENGINE=%r); main.py must import "
    "ui.lwc_host at module level, before QApplication" % (host.HAS_WEBENGINE,)
)
assert host.REGISTERED_BEFORE_QAPP is True, (
    "ndt:// scheme was not registered before QApplication "
    "(REGISTERED_BEFORE_QAPP=%r)" % (host.REGISTERED_BEFORE_QAPP,)
)
print("LWC_BOOTSTRAP_OK")
"""


class TestHostHasWebEngineAfterQApplication:
    """Subprocess probe: importing main first keeps HAS_WEBENGINE True."""

    def test_importing_main_keeps_webengine_available(self):
        env = dict(os.environ)
        env["QT_QPA_PLATFORM"] = "offscreen"
        env.pop("NDT_CHART_ENGINE", None)
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.run(
            [sys.executable, "-c", _PROBE],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=240,
        )
        assert proc.returncode == 0, (
            "bootstrap probe failed\n"
            f"--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}"
        )
        assert "LWC_BOOTSTRAP_OK" in proc.stdout
