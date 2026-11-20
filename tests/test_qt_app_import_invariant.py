"""ESC-126 (Q-79 follow-up): no import-time ``QApplication`` under ``tests/``.

Two P7-W4 suites used to create a dead module-level ``QApplication`` at import
(``tests/test_p7_w4_streaming.py:39``, ``tests/test_p7_w4_deferral.py:32``).
Collecting either before ``tests/test_lwc_render_smoke.py`` then made that
module's raw ``PyQt6.QtWebEngineWidgets`` import fail with
``ImportError: QtWebEngineWidgets must be imported or Qt.AA_ShareOpenGLContexts
must be set before a QCoreApplication instance is created``.

The fix is the Q-79 pattern: the app is created at **test time** by a
session-scoped autouse ``_qt_app`` fixture, never at import. This suite pins
the invariant three ways:

* statically, over every module in ``tests/`` (module scope only — a
  construction nested in a BooleanOp, a ternary or a module-level ``if`` still
  counts, one inside a function or class body does not);
* by collection in the escalated explicit order (each P7-W4 suite before the
  smoke suite), offscreen — exit 0 and no ``ImportError`` in the output;
* by test id: every case the two suites defined before the rework is still
  collected (the fix removed an import-time app and added a fixture; it
  deletes, renames and weakens no case).

``tests/test_lwc_render_smoke.py``'s own import order is deliberately not
touched here — P28/R-07 owns it.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = Path(__file__).resolve().parent

STREAMING = "tests/test_p7_w4_streaming.py"
DEFERRAL = "tests/test_p7_w4_deferral.py"
SMOKE = "tests/test_lwc_render_smoke.py"
P7_W4_FILES = (STREAMING, DEFERRAL)

#: Names whose *construction* at module scope is the invariant this suite pins.
_CONSTRUCTORS = frozenset({"QApplication", "QCoreApplication", "QGuiApplication"})

#: Every id ``tests/test_p7_w4_streaming.py`` defined before the ESC-126 rework
#: (13 cases: T11/T12/T13 as the module docstring records).
STREAMING_IDS = (
    "test_p7_t07_t11_replay_rebinds_reqids_without_bar_loss_or_dupes",
    "test_p7_t07_t11_manager_replay_rebounds_every_subscription",
    "test_p7_t07_t11_health_reaches_live_only_on_first_post_reconnect_bar",
    "test_p7_t07_t12_burst_keeps_priming_with_exact_once_ordering",
    "test_p7_t07_t13_no_blocking_sleep_on_any_pacing_path",
    "test_p7_t07_t13_every_pacing_handler_defers_without_blocking",
    "test_p7_t07_t13_wave_continuation_defers_and_resumes",
    "test_p7_t07_t13_prime_retry_defers_then_issues",
    "test_p7_t07_t13_prime_retry_boundary_fail_open_deterministic",
    "test_p7_t07_t13_prime_retry_fail_open_counts_skip",
    "test_p7_t07_t13_live_feed_attach_defers_via_singleshot",
    "test_p7_t07_t13_replay_all_defers_via_singleshot",
    "test_p7_t07_t13_backoff_progresses_and_retry_preserves_it",
)

#: Every id ``tests/test_p7_w4_deferral.py`` defined before the ESC-126 rework
#: (7 cases: T11/T12 as the module docstring records).
DEFERRAL_IDS = (
    "test_t11_watchlist_add_defers_under_throttle",
    "test_t11_watchlist_add_redefers_while_still_throttled",
    "test_t11_deferred_retry_dropped_after_remove",
    "test_t12_q41_source_scan_defers_never_sleeps",
    "test_t12_drive_watchlist_throttled_add",
    "test_t12_drive_live_feed_attach_throttled",
    "test_t12_drive_wave_continuation_and_prime_retry",
)


# ── Static scan ──────────────────────────────────────────────────────────────


def _callee_name(func_node) -> str | None:
    """The name a Call invokes: ``QApplication`` for both ``QApplication(...)``
    and ``QtWidgets.QApplication(...)``; ``instance`` for
    ``QApplication.instance()`` (a query, not a construction)."""
    if isinstance(func_node, ast.Name):
        return func_node.id
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    return None


def _module_level_constructor_calls(tree: ast.Module) -> list[ast.Call]:
    """Every application construction at module scope, in line order.

    Walks module-level statements (assignments, expressions, ``if``/``try``/
    ``with`` bodies, …) and **does not descend** into function, async function,
    class or lambda bodies. Nesting inside a BooleanOp or a ternary is still
    found because the walk is expression-deep.
    """
    found: list[ast.Call] = []
    stack: list[ast.AST] = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            continue  # never descend into a function or class body
        if isinstance(node, ast.Call) and _callee_name(node.func) in _CONSTRUCTORS:
            found.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return sorted(found, key=lambda node: (node.lineno, node.col_offset))


def _parse(rel: str) -> ast.Module:
    return ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _fixture_defs(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _is_session_autouse_fixture(node: ast.FunctionDef) -> bool:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if _callee_name(decorator.func) != "fixture":
            continue
        keywords = {kw.arg: kw.value for kw in decorator.keywords if kw.arg}
        scope = keywords.get("scope")
        autouse = keywords.get("autouse")
        if (
            isinstance(scope, ast.Constant)
            and scope.value == "session"
            and isinstance(autouse, ast.Constant)
            and autouse.value is True
        ):
            return True
    return False


def _body_constructs_application(node: ast.FunctionDef) -> bool:
    return any(
        isinstance(child, ast.Call)
        and _callee_name(child.func) in _CONSTRUCTORS
        for child in ast.walk(node)
    )


# ── AC1: the two P7-W4 suites ────────────────────────────────────────────────


@pytest.mark.parametrize("rel", P7_W4_FILES)
def test_p7_w4_module_scope_constructs_no_application(rel: str) -> None:
    """Neither suite builds a QApplication/QCoreApplication at import time."""
    offenders = [
        f"{rel}:{node.lineno}"
        for node in _module_level_constructor_calls(_parse(rel))
    ]
    assert offenders == [], (
        "import-time QApplication construction (ESC-126: collecting this "
        "module before tests/test_lwc_render_smoke.py breaks its "
        "QtWebEngineWidgets import): " + ", ".join(offenders)
    )


@pytest.mark.parametrize("rel", P7_W4_FILES)
def test_p7_w4_defines_session_autouse_qt_app_fixture(rel: str) -> None:
    """The app each suite needs is created at test time by ``_qt_app``."""
    fixture_def = _fixture_defs(_parse(rel)).get("_qt_app")
    assert fixture_def is not None, (
        f"{rel} defines no module-level `_qt_app` fixture — its widget "
        "construction would have no QApplication once the import-time app "
        "is gone"
    )
    assert _is_session_autouse_fixture(fixture_def), (
        f"{rel}::_qt_app must be @pytest.fixture(scope=\"session\", "
        "autouse=True) so every test in the module gets the app"
    )
    assert _body_constructs_application(fixture_def), (
        f"{rel}::_qt_app does not construct a QApplication — it must create "
        "the app at test time (Q-79 pattern)"
    )


# ── AC2: the invariant, tree-wide ────────────────────────────────────────────


def test_no_test_module_constructs_an_application_at_import() -> None:
    """No module under tests/ constructs an app at module scope."""
    modules = sorted(TESTS_DIR.glob("*.py"))
    assert modules, f"no test modules found under {TESTS_DIR}"
    offenders: list[str] = []
    for path in modules:
        rel = path.relative_to(REPO_ROOT).as_posix()
        offenders.extend(
            f"{rel}:{node.lineno}"
            for node in _module_level_constructor_calls(_parse(rel))
        )
    assert offenders == [], (
        "these modules construct a QApplication/QCoreApplication/"
        "QGuiApplication at import time — create it at test time from an "
        "autouse fixture instead (ESC-126): " + ", ".join(offenders)
    )


def test_scan_catches_boolop_ternary_and_module_level_if() -> None:
    """The scan is expression-deep at module scope and body-blind below it."""
    source = (
        "_APP = QApplication.instance() or QApplication([])\n"  # 1: direct
        "A = QApplication([]) if True else None\n"  # 2: ternary
        "if True:\n"  # 3
        "    _B = QCoreApplication([])\n"  # 4: module-level if body
        "def _f():\n"  # 5
        "    return QApplication([])\n"  # 6: function body — not import
        "class _C:\n"  # 7
        "    X = QGuiApplication([])\n"  # 8: class body — not import
    )
    assert [
        node.lineno for node in _module_level_constructor_calls(ast.parse(source))
    ] == [1, 2, 4]


# ── subprocess collection helpers ────────────────────────────────────────────


def _collect(args: list[str], quiet: bool) -> subprocess.CompletedProcess:
    """Run ``pytest --collect-only`` offscreen from the repo root.

    ``pytest 9``'s ``-q`` prints only per-file counts, so the id-comparing
    cases omit it and parse the node ids ``--collect-only`` prints.
    """
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    command = [sys.executable, "-m", "pytest", "--collect-only"]
    if quiet:
        command.append("-q")
    command.extend(args)
    return subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _collected_ids(rel: str) -> set[str]:
    proc = _collect([rel], quiet=False)
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        f"collection of {rel} failed (exit {proc.returncode}):\n"
        + output[-3000:]
    )
    return {
        line.strip().split("::", 1)[1]
        for line in proc.stdout.splitlines()
        if line.strip().startswith(rel + "::")
    }


# ── AC3: the escalated explicit collection orders ────────────────────────────


def test_escalated_collection_orders_do_not_break_the_smoke_suite() -> None:
    """Each P7-W4 suite collected *before* the smoke suite, offscreen."""
    failures: list[str] = []
    for p7_file in P7_W4_FILES:
        proc = _collect([p7_file, SMOKE], quiet=True)
        output = proc.stdout + proc.stderr
        markers = [
            marker
            for marker in (
                "ImportError",
                "must be imported or Qt.AA_ShareOpenGLContexts",
            )
            if marker in output
        ]
        if proc.returncode != 0 or markers:
            failures.append(
                f"{p7_file} then {SMOKE}: exit {proc.returncode}, "
                f"markers {markers}\n{output[-3000:]}"
            )
    assert failures == [], "\n\n".join(failures)


# ── AC4: no case deleted, renamed or weakened ────────────────────────────────


@pytest.mark.parametrize(
    ("rel", "expected"),
    [(STREAMING, STREAMING_IDS), (DEFERRAL, DEFERRAL_IDS)],
)
def test_pre_rework_test_ids_are_still_collected(
    rel: str, expected: tuple[str, ...]
) -> None:
    collected = _collected_ids(rel)
    missing = [test_id for test_id in expected if test_id not in collected]
    assert missing == [], (
        f"{rel} no longer collects these pre-rework ids (the ESC-126 fix "
        "must remove the import-time app and add a fixture, not delete or "
        "rename a case): " + ", ".join(missing)
    )
