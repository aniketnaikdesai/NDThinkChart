"""P27-T6 — every ``throttle`` double under ``tests/`` accepts the real call form.

D81 (``AC-D81.1``/``AC-D81.2``, S-P27-4) made
``PacingManager.throttle`` keyword-only on ``stamp``::

    def throttle(self, *, stamp: bool = True) -> bool:

and ``MarketDataManager``'s three request sites call
``throttle(stamp=False)`` (``req_mkt_data``, ``req_contract_details``,
``req_sec_def_opt_params``). A test harness that installs a zero-argument
replacement (``lambda: None``) therefore passes only for as long as nothing
reaches the generic request seam — the failure is latent, not absent, and the
option-stream suite proved it by aborting the interpreter inside a Qt slot when
the seam was finally reached.

This module is the durable half of that sweep: it discovers **every**
``throttle`` double in ``tests/`` from the tree at run time and fails unless
each one can be called as ``throttle()`` *and* ``throttle(stamp=False)``.
There is no allow-list and no exemption file — a double added by a later phase
is covered the moment it lands, and a zero-argument double cannot be
reintroduced without reddening this suite.

Two discovery shapes are recognised, because those are the two ways a double is
installed here:

* ``monkeypatch.setattr(<expr>, "throttle", <callable>)`` — the callable is
  checked in place, or resolved through a module-level name if it is a
  ``Name``/``Attribute``;
* ``def throttle(...)`` — a method on a test helper class.

The predicate ``accepts_keyword_stamp`` is deliberately *syntactic*, not a
runtime trial: it asks whether the callable declares ``stamp`` as a
keyword-only parameter **with a default** (so ``throttle()`` still works) or
declares ``**kwargs``. Anything it cannot resolve is a **failure**, never a
skip — an unresolvable double is exactly the case a future edit would produce.

``test_guard_rejects_zero_argument_doubles`` is the negative control: it feeds
the same predicate synthetic source in the pre-fix shape
(``lambda: None`` / ``monkeypatch.setattr(m, "throttle", lambda: None)``) and
asserts rejection, so this suite cannot pass by discovering nothing or by
accepting everything.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from pathlib import Path

import pytest

from ibkr.pacing import PacingManager

#: The directory the guard enumerates. Taken from this file so the guard keeps
#: working when the repo is checked out anywhere (no cwd assumption).
TESTS_DIR = Path(__file__).resolve().parent

#: The three suites whose installed double was changed from ``lambda: None`` to
#: ``lambda *, stamp=True: None`` (``AC-P27-06-3``). They must appear in the
#: discovered set, or the discovery itself is broken.
FIXED_SETATTR_FILES = (
    "tests/test_d65_option_stream.py",
    "tests/test_d27_reconnect.py",
    "tests/test_d45_removal.py",
)

#: The two class-based doubles that already carried ``*, stamp: bool = True`` —
#: the shape the predicate must accept (both named in the task's contract).
KEYWORD_DEF_FILES = (
    "tests/test_d65_option_chain.py",
    "tests/test_ibkr_contract_details_d22.py",
)


@dataclass(frozen=True)
class ThrottleDouble:
    """One ``throttle`` replacement found under ``tests/``.

    ``path`` is repo-relative (``tests/<module>.py``), ``lineno`` the line of
    the installing statement (for ``setattr``) or of the ``def`` (for a
    method), and ``kind`` records which of the two shapes it was.
    """

    path: str
    lineno: int
    kind: str  # "setattr" | "def"
    accepts_keyword_stamp: bool


def _params_accept_keyword_stamp(arguments: ast.arguments) -> bool:
    """True iff ``arguments`` can be called with ``stamp=<anything>``.

    Keyword-only ``stamp`` must carry a default, otherwise ``throttle()`` —
    the call every existing harness makes — would raise. ``**kwargs`` accepts
    the keyword by construction. A positional-or-keyword ``stamp`` is *not*
    accepted: D81's contract is that ``stamp`` is keyword-only, and a double
    that only happens to accept the keyword by position would drift from the
    real seam it stands in for.
    """
    if arguments.kwarg is not None:
        return True
    for name_node, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        if name_node.arg == "stamp" and default is not None:
            return True
    return False


def _callable_accepts(node: ast.AST) -> bool:
    if isinstance(node, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
        return _params_accept_keyword_stamp(node.args)
    return False


def _resolve_module_name(name: str, module: ast.Module) -> ast.AST | None:
    """Resolve ``name`` to its module-level definition/assignment value.

    Only module level is searched (the contract's rule): a double named through
    a local alias inside a function is unresolvable from the AST alone, and an
    unresolvable double must fail rather than be assumed correct.
    """
    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                return node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return node.value
    return None


def _resolve_attribute(attr: str, module: ast.Module) -> ast.AST | None:
    """Resolve ``<something>.throttle`` by the attribute name.

    The receiver is often an instance built elsewhere (``_PacingStub()``), so
    the receiver itself is not resolvable; the attribute name is matched
    against every function definition in the module, including methods inside
    helper classes. That is the only resolution a static pass can offer, and
    it is enough to find both class-based doubles in the tree.
    """
    for node in ast.walk(module):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == attr:
                return node
    return None


def accepts_keyword_stamp(expr: ast.AST, module_ast: ast.Module) -> bool:
    """Whether the callable expression ``expr`` accepts ``throttle(stamp=False)``.

    ``True`` for an inline lambda/def declaring keyword-only ``stamp`` with a
    default or ``**kwargs``, and for a ``Name``/``Attribute`` resolving to such
    a module-level definition. Everything else — including anything
    unresolvable — is ``False``.
    """
    if isinstance(expr, (ast.Lambda, ast.FunctionDef, ast.AsyncFunctionDef)):
        return _params_accept_keyword_stamp(expr.args)
    if isinstance(expr, ast.Name):
        resolved = _resolve_module_name(expr.id, module_ast)
        return resolved is not None and _callable_accepts(resolved)
    if isinstance(expr, ast.Attribute):
        resolved = _resolve_attribute(expr.attr, module_ast)
        return resolved is not None and _callable_accepts(resolved)
    return False


def _is_setattr_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "setattr"
    return isinstance(func, ast.Attribute) and func.attr == "setattr"


def doubles_in_source(source: str, path: str = "<synthetic>") -> list[ThrottleDouble]:
    """Discover the doubles in one module's source (used by the guard + tests).

    Kept separate from the filesystem walk so the negative control can exercise
    the *same* predicate over synthetic text without touching any real file.
    """
    try:
        module = ast.parse(source)
    except SyntaxError:  # pragma: no cover - a broken test module fails collection
        return []

    found: list[ThrottleDouble] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Call) and _is_setattr_call(node):
            if len(node.args) < 3:
                continue
            name_arg = node.args[1]
            if not (isinstance(name_arg, ast.Constant) and name_arg.value == "throttle"):
                continue
            found.append(
                ThrottleDouble(
                    path=path,
                    lineno=node.lineno,
                    kind="setattr",
                    accepts_keyword_stamp=accepts_keyword_stamp(node.args[2], module),
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "throttle":
                found.append(
                    ThrottleDouble(
                        path=path,
                        lineno=node.lineno,
                        kind="def",
                        accepts_keyword_stamp=_params_accept_keyword_stamp(node.args),
                    )
                )
    return found


def discover_throttle_doubles(tests_dir: Path) -> list[ThrottleDouble]:
    """Walk ``tests_dir`` and return every ``throttle`` double, sorted.

    ``path`` is relative to the tests directory's parent, i.e.
    ``tests/<module>.py``, so a failing case names the file a reader can open.
    """
    root = tests_dir.resolve().parent
    discovered: list[ThrottleDouble] = []
    for py_file in sorted(tests_dir.resolve().rglob("*.py")):
        rel = py_file.relative_to(root).as_posix()
        discovered.extend(doubles_in_source(py_file.read_text(encoding="utf-8"), rel))
    return sorted(discovered, key=lambda d: (d.path, d.lineno, d.kind))


_DISCOVERED = discover_throttle_doubles(TESTS_DIR)


# ---------------------------------------------------------------------------
# The guard
# ---------------------------------------------------------------------------


def test_real_throttle_signature_is_keyword_only_stamp():
    """``AC-P27-06-1``: read the live signature, not a copy of it."""
    signature = inspect.signature(PacingManager.throttle)
    parameters = list(signature.parameters.values())

    stamp = [p for p in parameters if p.name == "stamp"]
    assert len(stamp) == 1, f"throttle must declare 'stamp' exactly once, got {signature}"
    stamp_param = stamp[0]

    assert stamp_param.kind is inspect.Parameter.KEYWORD_ONLY, (
        f"throttle.stamp must be keyword-only, got {stamp_param.kind}: {signature}"
    )
    assert stamp_param.default is True, (
        f"throttle.stamp must default to True, got {stamp_param.default!r}: {signature}"
    )

    positional = [
        p.name
        for p in parameters
        if p.kind
        in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    assert "stamp" not in positional, (
        f"no parameter may accept 'stamp' positionally, got {positional}: {signature}"
    )


def _assert_required_files_present(found: list[ThrottleDouble]) -> None:
    present = {(d.path, d.kind) for d in found}
    for path in FIXED_SETATTR_FILES:
        assert (path, "setattr") in present, (
            f"discovery did not find the installed double in {path}; the guard "
            f"would be vacuous there. Discovered: {sorted(present)}"
        )
    for path in KEYWORD_DEF_FILES:
        assert (path, "def") in present, (
            f"discovery did not find the class-based throttle double in {path}; "
            f"the guard would be vacuous there. Discovered: {sorted(present)}"
        )


def test_discovery_covers_every_installed_double():
    """``AC-P27-06-2``: a non-empty, complete discovery — never a vacuous pass.

    The parametrized cases below cannot prove this on their own: an empty or
    truncated discovery would simply collect fewer (or zero) cases.
    """
    assert _DISCOVERED, f"no throttle double discovered under {TESTS_DIR}"
    _assert_required_files_present(_DISCOVERED)


@pytest.mark.parametrize(
    "double",
    _DISCOVERED,
    ids=[f"{d.path}:{d.lineno}" for d in _DISCOVERED],
)
def test_every_throttle_double_accepts_keyword_stamp(double: ThrottleDouble):
    """One case per discovered double: all must accept ``throttle(stamp=False)``."""
    _assert_required_files_present(_DISCOVERED)
    assert double.accepts_keyword_stamp, (
        f"{double.path}:{double.lineno} installs a {double.kind} 'throttle' double "
        f"that cannot be called as throttle(stamp=False). Use "
        f"'lambda *, stamp=True: None' (or 'def throttle(self, *, stamp=True)'), "
        f"not a zero-argument callable: the production seam calls it with the "
        f"keyword at req_mkt_data / req_contract_details / req_sec_def_opt_params."
    )


# ---------------------------------------------------------------------------
# Negative control — the guard must redden on the pre-fix shape
# ---------------------------------------------------------------------------

_PREFIX_SOURCE = """
x = lambda: None
monkeypatch.setattr(m, "throttle", lambda: None)
def throttle(self):
    return None
THROTTLE = lambda: None
monkeypatch.setattr(m, "throttle", THROTTLE)
monkeypatch.setattr(m, "throttle", unknown_callable)
"""

_FIXED_SOURCE = """
monkeypatch.setattr(m, "throttle", lambda *, stamp=True: None)
monkeypatch.setattr(m, "throttle", lambda **kwargs: None)
def throttle(self, *, stamp: bool = True):
    return None
def throttle(self, **kwargs):
    return None
THROTTLE = lambda *, stamp=True: None
monkeypatch.setattr(m, "throttle", THROTTLE)
"""


def _assignment_value(module: ast.Module, name: str) -> ast.AST:
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return node.value
    raise AssertionError(f"no module-level assignment to {name!r} in the control source")


def test_guard_rejects_zero_argument_doubles():
    """The predicate reddens on ``lambda: None`` — the pre-fix shape.

    Synthetic source only: no real test file is read or written here, so this
    cannot mask a real double and cannot go green because the tree happens to
    be clean. Both halves of the guard are exercised: the discovery over
    installed doubles, and the predicate over a bare ``x = lambda: None``.
    """
    rejected = doubles_in_source(_PREFIX_SOURCE, "<prefix>")
    accepted = doubles_in_source(_FIXED_SOURCE, "<fixed>")

    # Discovery: the installed ``setattr`` doubles and the ``def throttle``.
    # (``x = lambda: None`` is not an installed double, so it is not discovered;
    # it is checked through the predicate below.)
    assert len(rejected) == 4, f"negative control must see all 4 pre-fix doubles, got {rejected}"
    assert len(accepted) == 5, f"negative control must see all 5 fixed doubles, got {accepted}"

    red = [d for d in rejected if not d.accepts_keyword_stamp]
    assert len(red) == len(rejected), (
        "the guard accepted a zero-argument throttle double — it would pass "
        f"vacuously on the pre-fix tree: {[(d.lineno, d.kind) for d in rejected]}"
    )

    still_red = [d for d in accepted if not d.accepts_keyword_stamp]
    assert not still_red, (
        f"the guard rejected a keyword-compatible throttle double: "
        f"{[(d.lineno, d.kind) for d in still_red]}"
    )

    # The predicate itself, on the two bare-assignment forms the contract names.
    prefix_module = ast.parse(_PREFIX_SOURCE)
    assert not accepts_keyword_stamp(_assignment_value(prefix_module, "x"), prefix_module)
    assert not accepts_keyword_stamp(
        ast.parse("THROTTLE = lambda: None").body[0].value,
        ast.parse("THROTTLE = lambda: None"),
    )

    fixed_module = ast.parse(_FIXED_SOURCE)
    assert accepts_keyword_stamp(_assignment_value(fixed_module, "THROTTLE"), fixed_module)
    assert accepts_keyword_stamp(
        ast.parse("STAMPED = lambda *, stamp=True: None").body[0].value,
        ast.parse("STAMPED = lambda *, stamp=True: None"),
    )
