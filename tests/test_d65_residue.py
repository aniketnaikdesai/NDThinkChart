"""P23-T13 — the standing Unused-Code Rule gate (S-P23-15) and the D65 batch gate.

Two instruments in one suite, because "nothing unused remains" can fail in two
different places and each needs its own net:

1. **The standing gate's five clauses** (``AC-D65.12``), run over the finished
   P23 tree *and* re-run over a seeded fixture so the gate is proven capable of
   going red before anyone trusts it green:

   (i)   every P23 symbol has a production caller or a cited registration site;
   (ii)  every P23 test helper is referenced in its own file;
   (iii) no unused import / unreached branch / ``if False`` / ``noqa``-silenced
         import / commented-out implementation block / ``__all__``-only export /
         "keep for later" module in the files P23 authored;
   (iv)  every new signal is both emitted **and** connected;
   (v)   EWrapper / Qt name-invoked callbacks are allowlisted with the
         registration site that invokes them.

   The scanners below are pure functions over ``{path: source}`` maps, so the
   fixture case exercises *the same code the tree case runs* — a separate
   fixture assertion could drift from the real gate and prove nothing.

2. **The displaced-token and batch-gate half** (``AC-D65.11``/``.13``/``.1``,
   ``AC-D65.19`` left open): P23-T12's forbidden-token additions are absent
   from the tree, the KEEP ledger names each surviving consumer, AC-D65.1's own
   dock measurable is re-run, the D41–D64 history is intact, and the gate record
   names the three owner-authorised pre-P23 edits, S-P23-24's recorded
   consequence and the still-open paper-TWS criterion.

   The token sweep carries **one narrow carve-out**, and the carve-out is
   machine-checked rather than a blanket amnesty: an entry must actually contain
   a displaced token (``test_every_carve_out_entry_is_earned``), and the entries
   are the two forbidden-token tables plus the suites whose job is to *spell* a
   name in order to assert its absence. The three dropped table names are
   deliberately **not** tokens — the migration's ``DROP`` and the schema-absence
   assertions must spell them, which is how AC-D65.18 measures them.

Full-suite green is a batch-gate action (run the suite), never a case here: a
case that shells out to pytest would recurse.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from PyQt6.QtWidgets import QStyledItemDelegate

from ibapi.wrapper import EWrapper

REPO = Path(__file__).resolve().parent.parent
SOURCE_DIRS = ("ui", "services", "data", "ibkr", "config")
TEST_DIR = "tests"

# ---------------------------------------------------------------------------
# The P23 file sets
# ---------------------------------------------------------------------------

#: The modules P23 created. Their public symbols are the census's first half.
P23_NEW_MODULES = (
    "ui/option_spreads_panel.py",
    "services/option_ladder.py",
    "services/option_spread_engine.py",
    "data/db_backup.py",
)

#: The symbols P23 added to modules that already existed. Named explicitly (a
#: diff against the pre-P23 baseline would tie the gate to git state, and the
#: gate has to run on a plain checkout).
P23_ADDED_SYMBOLS = {
    "ibkr/bridge.py": (
        "option_params", "option_params_end", "option_computation",
    ),
    "ibkr/subscription_manager.py": ("OPTION_LEGS",),
    "ibkr/market_data.py": ("req_sec_def_opt_params",),
    "ibkr/contracts.py": (
        "OptionSeries", "get_option_contract", "today_expiry_yyyymmdd",
        "select_zero_dte_series", "option_chain_strikes",
        "SPX_OPTION_SYMBOL", "SPX_OPTION_TRADING_CLASS", "SPX_OPTION_EXCHANGE",
        "SPX_OPTION_CURRENCY", "SPX_OPTION_MULTIPLIER",
    ),
}

#: The five new phase suites + this one. Clause (ii) scans their helpers.
P23_SUITES = (
    "tests/test_d65_option_chain.py",
    "tests/test_d65_option_ladder.py",
    "tests/test_d65_option_panel.py",
    "tests/test_d65_option_stream.py",
    "tests/test_d65_spread_engine.py",
    "tests/test_d65_residue.py",
)

#: Clause (iii) is scoped to the files P23 *authored*: the four new modules and
#: its suites. The legacy modules P23 edited carry pre-existing unused imports
#: (`ui/main_window.py` has six, `ibkr/client.py` re-exports IBKRNotReady through
#: __all__) that no P23 task owns; flagging them here would redden the gate on
#: debt this wave does not own, which is precisely what AC-D65.12's measurable
#: must not do. A P23-introduced unused import in a new module is still caught.
P23_AUTHORED_FILES = P23_NEW_MODULES + P23_SUITES

# ---------------------------------------------------------------------------
# Clause (i) — the census allowlist, each entry with its cited site
# ---------------------------------------------------------------------------

#: Symbols that are live *because a framework or a contract invokes them by
#: name*, never because Python code calls them. Every value is the citation,
#: and every citation is re-checked by the suite (see
#: ``test_census_allowlist_cites_a_live_site``) — a stale entry fails.
CENSUS_ALLOWLIST = {
    "services/option_spread_engine.py": {
        # The published contract names the engine `OptionSpreadEngine`
        # (`docs/tasks/task-graph.json`, P23-T7's signature). The module keeps
        # that name as an alias of the class it renamed to `SpreadEngine`; the
        # comment above the alias records the same thing.
        "OptionSpreadEngine": (
            "docs/tasks/task-graph.json P23-T7 signature "
            "`class OptionSpreadEngine`"
        ),
    },
}

#: Clause (v) — EWrapper callbacks: ibapi's reader thread dispatches by method
#: name, so no Python call site exists to find. The registration site is the
#: installed wheel's `EWrapper` attribute of the same name (asserted below).
EWRAPPER_CALLBACKS = {
    "tickOptionComputation": (
        "EWrapper.tickOptionComputation — invoked by name from ibapi's dispatch"
    ),
    "securityDefinitionOptionParameter": (
        "EWrapper.securityDefinitionOptionParameter — invoked by name from "
        "ibapi's dispatch"
    ),
    "securityDefinitionOptionParameterEnd": (
        "EWrapper.securityDefinitionOptionParameterEnd — invoked by name from "
        "ibapi's dispatch"
    ),
}

#: Clause (v) — Qt callbacks: the view invokes these through the delegate's
#: virtual slots, not from Python. The base-class attribute is the registry.
QT_CALLBACKS = {
    ("ui/option_spreads_panel.py", "initStyleOption"): QStyledItemDelegate,
    ("ui/option_spreads_panel.py", "sizeHint"): QStyledItemDelegate,
}

#: Clause (iv) — the signals P23 added, and the two files at either end.
P23_SIGNALS = ("option_params", "option_params_end", "option_computation")
SIGNAL_EMITTER = "ibkr/client.py"
SIGNAL_CONSUMER = "ui/main_window.py"

# ---------------------------------------------------------------------------
# The displaced tokens (P23-T12's additions to the forbidden set)
# ---------------------------------------------------------------------------

#: Exactly the names P23-T12 appended to `tests/test_d45_removal.py::_FORBIDDEN`
#: (its "added by P23 (D65)" block). The suite asserts the two lists agree, so
#: neither can drift silently.
DISPLACED_TOKENS = (
    "ActivePortfolioPanel",
    "portfolio_panel",
    "Account Summary",
    "account_summary",
    "account_summary_end",
    "position_update",
    "position_end",
    "build_position_from_ib",
    "_parse_contract_type",
    "detect_and_group",
    "OptionLeg",
    "strategy_detection",
    "Position",
    "TradeGroup",
    "_upsert_position",
    "_symbol_last_prices",
    "_record_symbol_price",
    "set_price_sink",
    "_price_sink",
    "reqAccountSummary",
    "reqPositions",
    "_account_id",
)

#: Files whose *job* is to spell a displaced name. Two kinds, both narrow:
#:  * the forbidden-token tables (`_FORBIDDEN`/`_SURVIVORS`/`_RETIRED_TABLES`) —
#:    a token table cannot name what it forbids without naming it;
#:  * the absence assertions, which must spell a dropped signal, model or panel
#:    name to prove it gone (`hasattr(...) is False`, `!= "Portfolio"`, the
#:    EWrapper override census). Removing these would not clean the tree, it
#:    would delete the proof.
#: `test_every_carve_out_entry_is_earned` fails any entry that no longer needs
#: the carve-out.
TOKEN_CARVE_OUT = (
    "tests/test_d45_removal.py",
    "tests/test_d65_residue.py",
    "tests/test_d65_option_chain.py",
    "tests/test_d65_option_panel.py",
    "tests/test_ui_smoke.py",
)

#: Two names are ordinary English words whose substrings appear inside Qt and
#: ibapi identifiers (`sectionViewportPosition`), so they are matched as whole
#: units — the same treatment `tests/test_d45_removal.py` gives `orders`/`Orders`.
_TOKEN_EXACT_ONLY = frozenset({"Position", "TradeGroup"})
_TOKEN_MIN_SUBSTRING = 6
_TOKEN_SPLIT = re.compile(r"[^0-9A-Za-z_]+")

# The consistency claims — stated identically in the plan, the architecture and
# the new suites (AC-D65.4/.6/.2/.3).
CONSISTENCY_FILES = (
    "docs/plan.md",
    "docs/architecture.md",
) + P23_SUITES[:-1]

CANONICAL_FIXTURES = ("7425/7445", "7340/7320")
BANNED_EXAMPLES = ("7425/7435", "7315/7435")
LEGAL_NON_BANNED_PAIR = "7435/7455"
OPTION_CAP = 16
SPOT_TOTAL = 17

_CLAIM_MARKERS = (
    "ban", "typo", "reject", "raises", "never", "10-wide", "inverted",
    "not 20", "guard", "banned",
)

# ---------------------------------------------------------------------------
# The batch gate record (AC-D65.11/.13, AC-D65.19 left open)
# ---------------------------------------------------------------------------

GATE_RECORD = """\
D65 (P23) batch gate record — built by P23-T13 (generation 0), on the finished
P23 working tree (P23-01 … P23-12 landed).

Full offscreen suite
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ --tb=no -q -o addopts=""
    => 3 failed, 1682 passed, 3 skipped in 87.55s
    * tests/test_d65_option_chain.py::test_no_production_caller_outside_ibkr and
      ::test_account_and_position_overrides_and_signals_remain — pre-existing,
      outside this task's footprint, and owned by their task: both assert
      contracts an earlier P23 wave deliberately deleted, so their fix belongs
      to that contract's owner, not to this gate.
    * tests/test_d64_batch_gate.py::test_p22_t5_ac2_shared_seam_record — an
      environment artefact of the uncommitted wave, not a T13 defect: its DG116
      clause asserts that no tracked file under tests/ differs from HEAD, and the
      P23 working tree still carries every wave's test edits uncommitted. This
      task contributes nothing to it (`tests/test_d65_residue.py` is untracked;
      usage.md and services/option_ladder.py sit outside tests/), so it clears
      when the phase commits.
    The 35 cases in tests/test_d65_residue.py all pass, including the two that
    drive the seeded dead-symbol / unconnected-signal fixture.

The three owner-authorised pre-P23 edits (a recorded git note, per the plan —
these are asserted by this record, never by a test)
    1. The D41 title re-points — every surviving title-keyed right-dock consumer
       now keys on the dock's objectName(); no dock title is a lookup key.
    2. A194's supersession — the Portfolio/account-position stack is superseded
       by the Option Spreads panel; the panel, its ten call sites and the whole
       account plane are deleted, not re-pointed.
    3. A201's D18 launch-width amendment with its two re-baselines — the right
       dock launches at the panel's 360 px preferred width and the two D18
       baselines were re-taken for that width.

The one recorded phase-internal consequence (S-P23-24 — not a fourth edit)
    D26.5's paper/live badge derivation retired with the account path. Its
    reason: the badge's only account-typed inputs died with the account plane in
    P23-06, and the port guard proves the port alone — it cannot prove which kind
    of account is logged in — so the honest claim is "● Connected". It edits no
    requirements.md text, which is why AC-D65.11's three records stand as three.

Bookkeeping (each re-checked by a case in this suite)
    * tests/conftest.py names no dropped table.
    * tests/test_p13_gate.py's ui/*.py allowlist holds option_spreads_panel.py
      and not active_portfolio_panel.py.
    * tests/test_d45_removal.py holds no test whose subject is deleted.
    * AC-D65.11's marker grep and the D41–D64 history sections hold.

Open criterion — NOT claimed by this gate
    AC-D65.19 (the owner's paper-TWS acceptance run) is still OPEN and is owned
    by P23-T14. The build can observe every other AC-D65.* criterion; it cannot
    observe a live paper-TWS session, and this record claims exactly that.
"""

# ---------------------------------------------------------------------------
# loading + the pure scanners
# ---------------------------------------------------------------------------

_SOURCE_CACHE: dict[str, str] | None = None


def _text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def sources() -> dict[str, str]:
    """Every Python source the gate measures, keyed by repo-relative path."""
    global _SOURCE_CACHE
    if _SOURCE_CACHE is None:
        out: dict[str, str] = {}
        for directory in (*SOURCE_DIRS, TEST_DIR):
            for path in sorted((REPO / directory).rglob("*.py")):
                out[path.relative_to(REPO).as_posix()] = path.read_text(
                    encoding="utf-8"
                )
        _SOURCE_CACHE = out
    return _SOURCE_CACHE


def _defined_symbols(text: str) -> tuple[str, ...]:
    """Public top-level names a module *offers*: defs, classes, constants."""
    names: list[str] = []
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.append(target.id)
    return tuple(names)


def _load_names(text: str) -> set[str]:
    """Names the file *uses*: loaded names, attribute names, import aliases.

    Definition names are deliberately excluded — a `def`/`class` name and an
    assignment target are not references, so a symbol that only exists cannot
    pass the census by existing.
    """
    used: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
            value = node
            while isinstance(value, ast.Attribute):
                value = value.value
            if isinstance(value, ast.Name):
                used.add(value.id)
        elif isinstance(node, ast.alias):
            used.add(node.name)
            used.add((node.asname or node.name).split(".")[-1])
    return used


def _mention_names(text: str) -> set[str]:
    """Everything a file mentions — definitions included, strings included."""
    mentioned: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Name):
            mentioned.add(node.id)
        elif isinstance(node, ast.Attribute):
            mentioned.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            mentioned.add(node.name)
        elif isinstance(node, ast.arg):
            mentioned.add(node.arg)
        elif isinstance(node, ast.alias):
            mentioned.add(node.name)
            mentioned.add((node.asname or node.name).split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            mentioned.add(node.value)
    return mentioned


def scan_unreferenced_symbols(
    tree: dict[str, str],
    candidates: dict[str, tuple[str, ...]],
    allowlist: dict[str, dict[str, str]] | None = None,
) -> list[str]:
    """Clause (i): `module:symbol` for every candidate nothing references.

    "Referenced" means a load/attribute/import mention in any *other* file, or
    a use inside its own module beyond the definition itself. An allowlisted
    symbol needs a cited registration site instead, and the caller checks the
    citation.
    """
    allowlist = allowlist or {}
    used = {path: _load_names(text) for path, text in tree.items()}
    mentioned = {path: _mention_names(text) for path, text in tree.items()}
    violations: list[str] = []
    for module, symbols in candidates.items():
        for symbol in symbols:
            if symbol in allowlist.get(module, {}):
                continue
            if symbol in used.get(module, set()):
                continue
            if any(
                symbol in mentioned[path] for path in tree if path != module
            ):
                continue
            violations.append(f"{module}:{symbol}")
    return sorted(violations)


_SIGNAL_DEF_RE = re.compile(r"^[ \t]*(\w+)\s*=\s*pyqtSignal\(", re.MULTILINE)


def scan_unbalanced_signals(
    tree: dict[str, str], names: tuple[str, ...] | None = None
) -> list[str]:
    """Clause (iv): signals with no `.emit(` or no `.connect(` anywhere."""
    if names is None:
        discovered: list[str] = []
        for text in tree.values():
            discovered.extend(_SIGNAL_DEF_RE.findall(text))
        names = tuple(discovered)
    violations: list[str] = []
    blob = "\n".join(tree.values())
    for name in names:
        emitted = re.search(rf"\.{re.escape(name)}\.emit\(", blob) is not None
        connected = re.search(rf"\.{re.escape(name)}\.connect\(", blob) is not None
        if not (emitted and connected):
            violations.append(
                f"{name}: emitted={emitted} connected={connected}"
            )
    return violations


def scan_unused_imports(text: str) -> list[tuple[int, str]]:
    """Clause (iii): imports whose bound name is never used in the file."""
    tree = ast.parse(text)
    imported: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "__future__":
                    continue
                imported[alias.asname or alias.name.split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                imported[alias.asname or alias.name] = node.lineno
    used = _load_names(text)
    return sorted(
        (lineno, name) for name, lineno in imported.items() if name not in used
    )


def scan_noqa_imports(text: str) -> list[int]:
    """Clause (iii): a `# noqa` that hides an import the file never uses.

    AST-based on purpose, and tied to the unused-import set on purpose. An
    `import` inside a string literal (a subprocess probe's script) is text, not
    this file's import, so it is not residue; and a `# noqa` on an import whose
    module the file really uses suppresses no dead code. The clause targets the
    suppression that hides residue, which is what `# noqa: F401` on a dead
    import is — not every lint pragma in the tree.
    """
    unused = {lineno for lineno, _ in scan_unused_imports(text)}
    lines = text.splitlines()
    hits: list[int] = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        lineno = node.lineno
        if lineno not in unused or not (0 < lineno <= len(lines)):
            continue
        if "# noqa" in lines[lineno - 1]:
            hits.append(lineno)
    return sorted(set(hits))


_TERMINATORS = (ast.Return, ast.Raise, ast.Continue, ast.Break)


def scan_unreachable(text: str) -> list[int]:
    """Clause (iii): `if False`/`while False` and statements after a terminator."""
    hits: list[int] = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.If, ast.While)):
            test = node.test
            if isinstance(test, ast.Constant) and not test.value:
                hits.append(node.lineno)
        body = getattr(node, "body", None)
        if isinstance(body, list):
            terminated = False
            for statement in body:
                if terminated:
                    hits.append(getattr(statement, "lineno", 0))
                if isinstance(statement, _TERMINATORS):
                    terminated = True
    return sorted(hits)


_CODE_STARTS = (
    "import ", "from ", "def ", "class ", "return ", "if ", "for ", "while ",
    "with ", "assert ", "raise ", "try:", "print(", "self.", "await ", "yield ",
)


def scan_commented_out_blocks(text: str) -> list[int]:
    """Clause (iii): a >=3-line `#` run that is, in fact, parseable code."""
    hits: list[int] = []
    run: list[tuple[int, str]] = []
    for lineno, line in enumerate([*text.splitlines(), ""], start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            run.append((lineno, stripped.lstrip("#").strip()))
            continue
        if len(run) >= 3:
            body = "\n".join(piece for _, piece in run)
            try:
                ast.parse(body)
            except SyntaxError:
                parseable = False
            else:
                parseable = True
            if parseable and body.startswith(_CODE_STARTS):
                hits.append(run[0][0])
        run = []
    return hits


def scan_all_only_exports(text: str, tree: dict[str, str], module: str) -> list[str]:
    """Clause (iii): an `__all__` name with no use and no other-file mention."""
    tree = {**tree, module: text}
    used = _load_names(text)
    mentioned = {
        path: _mention_names(source) for path, source in tree.items()
    }
    violations: list[str] = []
    for node in ast.parse(text).body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(getattr(t, "id", None) == "__all__" for t in node.targets):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for element in node.value.elts:
            if not isinstance(element, ast.Constant):
                continue
            name = element.value
            if name in used:
                continue
            if any(name in mentioned[p] for p in tree if p != module):
                continue
            violations.append(f"{module}:{name} (__all__-only)")
    return violations


def _token_matches(name: str) -> str | None:
    """The displaced token `name` carries, or None (mirrors the D45 instrument)."""
    parts = _TOKEN_SPLIT.split(name)
    for token in DISPLACED_TOKENS:
        if token in _TOKEN_EXACT_ONLY:
            if name == token:
                return token
        elif len(token) >= _TOKEN_MIN_SUBSTRING:
            if token in name:
                return token
        elif name == token or token in parts:
            return token
    return None


def _token_offences(text: str) -> set[str]:
    idents, strings = set(), set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Name):
            idents.add(node.id)
        elif isinstance(node, ast.Attribute):
            idents.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            idents.add(node.name)
        elif isinstance(node, ast.arg):
            idents.add(node.arg)
        elif isinstance(node, ast.keyword) and node.arg:
            idents.add(node.arg)
        elif isinstance(node, ast.alias):
            idents.add(node.name)
            idents.add((node.asname or node.name).split(".")[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    return {
        token
        for token in (_token_matches(n) for n in idents | strings)
        if token
    }


def _negative_assertion(line: str) -> bool:
    return "!=" in line or "not in" in line or "is None" in line


# ---------------------------------------------------------------------------
# Clause (i) — every P23 symbol has a caller or a cited registration site
# ---------------------------------------------------------------------------


def _census_candidates(tree: dict[str, str]) -> dict[str, tuple[str, ...]]:
    candidates: dict[str, tuple[str, ...]] = {}
    for module in P23_NEW_MODULES:
        candidates[module] = _defined_symbols(tree[module])
    for module, extra in P23_ADDED_SYMBOLS.items():
        candidates[module] = tuple(candidates.get(module, ())) + extra
    return candidates


def test_every_p23_symbol_has_a_caller_or_a_cited_registration_site():
    tree = sources()
    violations = scan_unreferenced_symbols(
        tree, _census_candidates(tree), CENSUS_ALLOWLIST
    )
    assert not violations, (
        "P23 symbols with no caller and no cited registration site: "
        f"{violations}"
    )


def test_census_allowlist_cites_a_live_site():
    """No allowlist entry may be a bare name — each citation must resolve."""
    tree = sources()
    candidates = _census_candidates(tree)
    for module, entries in CENSUS_ALLOWLIST.items():
        assert module in candidates, f"allowlist names an unscanned module: {module}"
        for symbol, citation in entries.items():
            assert citation.strip(), f"{module}:{symbol} has an empty citation"
            assert symbol in _text("docs/tasks/task-graph.json"), (
                f"{module}:{symbol} cites {citation!r}, but the contract does "
                "not name it"
            )
            assert symbol in _text(module), (
                f"{module}:{symbol} is allowlisted but the module no longer "
                "defines it"
            )


# ---------------------------------------------------------------------------
# Clause (ii) — every P23 test helper is referenced in its own file
# ---------------------------------------------------------------------------


def _unreferenced_helpers(text: str) -> list[str]:
    tree = ast.parse(text)
    referenced = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            referenced.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            referenced.add(node.value)
    missing: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        name = node.name
        if not name.startswith("_") or name.startswith("__"):
            continue
        if name not in referenced:
            missing.append(name)
    return missing


def test_every_p23_test_helper_is_referenced_in_its_file():
    violations = []
    for suite in P23_SUITES:
        for helper in _unreferenced_helpers(_text(suite)):
            violations.append(f"{suite}:{helper}")
    assert not violations, f"unreferenced test helpers: {violations}"


# ---------------------------------------------------------------------------
# Clause (iii) — no unused import / unreal branch / dead block in P23 files
# ---------------------------------------------------------------------------


def test_no_unused_import_and_no_noqa_silenced_import():
    violations = []
    for rel in P23_AUTHORED_FILES:
        text = _text(rel)
        for lineno, name in scan_unused_imports(text):
            violations.append(f"{rel}:{lineno}: unused import {name}")
        for lineno in scan_noqa_imports(text):
            violations.append(f"{rel}:{lineno}: noqa-silenced import")
    assert not violations, f"import residue: {violations}"


def test_no_unreachable_branch_or_if_false():
    violations = []
    for rel in P23_AUTHORED_FILES:
        for lineno in scan_unreachable(_text(rel)):
            violations.append(f"{rel}:{lineno}")
    assert not violations, f"unreachable code: {violations}"


def test_no_commented_out_implementation_block():
    violations = []
    for rel in P23_AUTHORED_FILES:
        for lineno in scan_commented_out_blocks(_text(rel)):
            violations.append(f"{rel}:{lineno}")
    assert not violations, f"commented-out blocks: {violations}"


def test_no_all_only_export():
    tree = sources()
    violations = []
    for rel in P23_AUTHORED_FILES:
        violations.extend(scan_all_only_exports(_text(rel), tree, rel))
    assert not violations, f"__all__-only exports: {violations}"


def test_no_keep_for_later_module():
    tree = sources()
    violations = []
    for module in P23_NEW_MODULES:
        stem = Path(module).stem
        imported_elsewhere = any(
            stem in source
            for path, source in tree.items()
            if path != module
        )
        if not imported_elsewhere:
            violations.append(f"{module}: no importer (keep-for-later module)")
    assert not violations, f"orphan modules: {violations}"


# ---------------------------------------------------------------------------
# Clauses (iv) and (v) — signals and name-invoked callbacks
# ---------------------------------------------------------------------------


def test_every_new_signal_is_emitted_and_connected():
    violations = scan_unbalanced_signals(sources(), P23_SIGNALS)
    assert not violations, f"unbalanced P23 signals: {violations}"
    assert ".option_params.emit(" in _text(SIGNAL_EMITTER)
    assert ".option_params.connect(" in _text(SIGNAL_CONSUMER)


def test_ewrapper_callbacks_are_allowlisted_with_their_registration_site():
    for name, site in EWRAPPER_CALLBACKS.items():
        assert site and name in site, (
            f"{name}: the allowlist entry does not cite the registration site"
        )
        assert hasattr(EWrapper, name), (
            f"{name}: cited as an EWrapper callback, but the installed ibapi "
            "wheel has no such attribute — the registration site is gone"
        )
    overrides = _ewrapper_overrides()
    missing = sorted(set(overrides) - set(EWRAPPER_CALLBACKS))
    assert not missing, (
        "P23 EWrapper overrides with no allowlist entry: "
        f"{missing} — register them with their registration site"
    )


def _ewrapper_overrides() -> list[str]:
    tree = ast.parse(_text("ibkr/client.py"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "IBApiClient":
            return [
                child.name
                for child in node.body
                if isinstance(child, ast.FunctionDef)
                and hasattr(EWrapper, child.name)
                and child.name in EWRAPPER_CALLBACKS
            ]
    return []


def test_qt_callbacks_are_allowlisted_with_their_registration_site():
    for (module, name), base in QT_CALLBACKS.items():
        assert hasattr(base, name), (
            f"{module}:{name} is cited as a {base.__name__} override, but the "
            "base class no longer declares it"
        )
        assert re.search(rf"def {re.escape(name)}\(", _text(module)), (
            f"{module}:{name} is allowlisted but no longer defined"
        )


# ---------------------------------------------------------------------------
# The gate must be RED on a seeded fixture before it is trusted green
# ---------------------------------------------------------------------------


@pytest.fixture()
def dead_fixture(tmp_path):
    """A tiny tree holding an uncalled function and an unconnected signal."""
    (tmp_path / "dead_module.py").write_text(
        "from PyQt6.QtCore import QObject, pyqtSignal\n\n\n"
        "class DeadOwner(QObject):\n"
        "    dead_signal = pyqtSignal(int)\n\n\n"
        "def leftover_helper(value):\n"
        "    return value\n",
        encoding="utf-8",
    )
    (tmp_path / "user_module.py").write_text(
        "from dead_module import DeadOwner\n\n\n"
        "def poke(owner):\n"
        "    owner.dead_signal.emit(1)\n",
        encoding="utf-8",
    )
    return {
        "dead_module.py": (tmp_path / "dead_module.py").read_text(encoding="utf-8"),
        "user_module.py": (tmp_path / "user_module.py").read_text(encoding="utf-8"),
    }


def test_gate_is_red_on_a_seeded_dead_symbol(dead_fixture):
    census = scan_unreferenced_symbols(
        dead_fixture, {"dead_module.py": ("leftover_helper",)}
    )
    assert census == ["dead_module.py:leftover_helper"], (
        "the census must see the uncalled fixture function"
    )


def test_gate_is_red_on_a_seeded_unconnected_signal(dead_fixture):
    unbalanced = scan_unbalanced_signals(dead_fixture)
    assert unbalanced == ["dead_signal: emitted=True connected=False"], (
        "the signal scan must see the fixture's unconnected signal"
    )


def test_gate_is_green_on_the_tree_only_after_it_is_red_on_the_fixture(dead_fixture):
    """The failing-before/passing-after rule, in one assertion pair."""
    assert scan_unreferenced_symbols(
        dead_fixture, {"dead_module.py": ("leftover_helper",)}
    ), "seeded fixture did not make the gate red"
    assert not scan_unreferenced_symbols(
        sources(), _census_candidates(sources()), CENSUS_ALLOWLIST
    ), "the real tree must be green"


# ---------------------------------------------------------------------------
# The displaced-token sweep (AC-D65.13) and its narrow carve-out
# ---------------------------------------------------------------------------


def _production_offences() -> list[str]:
    violations = []
    for rel, text in sources().items():
        if not rel.split("/")[0] in SOURCE_DIRS:
            continue
        for token in sorted(_token_offences(text)):
            violations.append(f"{rel}:{token}")
    return violations


def _test_offences_outside_carve_out() -> list[str]:
    violations = []
    for rel, text in sources().items():
        if not rel.startswith(TEST_DIR + "/") or rel in TOKEN_CARVE_OUT:
            continue
        for token in sorted(_token_offences(text)):
            violations.append(f"{rel}:{token}")
    return violations


def test_displaced_tokens_are_absent_from_the_production_tree():
    violations = _production_offences()
    assert not violations, f"live displaced tokens in production: {violations}"


def test_displaced_tokens_are_absent_from_tests_outside_the_carve_out():
    violations = _test_offences_outside_carve_out()
    assert not violations, (
        "displaced tokens live in tests outside the documented carve-out: "
        f"{violations}"
    )


def test_every_carve_out_entry_is_earned():
    """A carve-out that no longer needs it is amnesty — fail it."""
    stale = []
    for rel in TOKEN_CARVE_OUT:
        if not _token_offences(_text(rel)):
            stale.append(rel)
    assert not stale, f"carve-out entries that no longer spell a token: {stale}"


def test_the_d45_table_carries_the_p23_displacements():
    """Both token lists are the same list; neither may drift alone."""
    tree = ast.parse(_text("tests/test_d45_removal.py"))
    forbidden: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "_FORBIDDEN" for t in node.targets
        ):
            forbidden = {
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant)
            }
    assert forbidden, "tests/test_d45_removal.py no longer defines _FORBIDDEN"
    missing = sorted(set(DISPLACED_TOKENS) - forbidden)
    assert not missing, f"tokens this gate sweeps but the D45 table lost: {missing}"


KEEP_LEDGER_FILE = "docs/plan.md"
KEEP_LEDGER_MARKER = "**KEEP (with the surviving consumer, and why):**"

#: (symbol named in the ledger, consumer wording that must sit beside it, a live
#: production path where the symbol is really used). AC-D65.13 demands that each
#: KEEP entry names the surviving consumer; the last element proves the reason
#: is not prose about a dead symbol.
KEEP_ENTRIES = (
    ("IdManager.get_id", "market-data callers", "ibkr/market_data.py"),
    ("classify_error", "error surface", "ibkr/client.py"),
    ("SubscriptionManager", "registry", "ui/main_window.py"),
    ("Option Spreads", "right dock", "ui/main_window.py"),
    ("dock_layout.py", "width model", "ui/main_window.py"),
    ("visual_conventions.py", "collapse header", "ui/main_window.py"),
    ("md_line_guard.py", "budget", "ui/main_window.py"),
    ("config/paths.py", "backup directory", "data/db_backup.py"),
)


def _keep_ledger_block() -> str:
    text = _text(KEEP_LEDGER_FILE)
    assert KEEP_LEDGER_MARKER in text, (
        f"{KEEP_LEDGER_FILE} lost the KEEP ledger ({KEEP_LEDGER_MARKER})"
    )
    start = text.index(KEEP_LEDGER_MARKER)
    end = text.find("\n\n", start)
    return text[start:end if end != -1 else len(text)]


def test_every_keep_entry_names_its_surviving_consumer():
    block = _keep_ledger_block()
    # The ledger is a semicolon-separated list, and its prose wraps: flatten
    # the whitespace first, then hold each entry to its own segment so one
    # printed line break (or a consumer named before its symbol) is not read as
    # a missing reason.
    segments = [" ".join(part.split()) for part in block.split(";")]
    violations = []
    for symbol, consumer, live_path in KEEP_ENTRIES:
        segment = next((part for part in segments if symbol in part), None)
        if segment is None:
            violations.append(f"{symbol}: missing from the KEEP ledger")
            continue
        if consumer not in segment:
            violations.append(
                f"{symbol}: recorded reason does not name {consumer!r}"
            )
        haystack = _text(live_path) if symbol != "md_line_guard.py" else (
            _text("ui/main_window.py") + _text("services/md_line_guard.py")
        )
        probe = {
            "IdManager.get_id": "get_id",
            "classify_error": "classify_error",
            "SubscriptionManager": "SubscriptionManager",
            "Option Spreads": "OptionSpreadsPanel",
            "dock_layout.py": "dock_layout",
            "visual_conventions.py": "visual_conventions",
            "md_line_guard.py": "md_line_guard",
            "config/paths.py": "config.paths",
        }[symbol]
        if probe not in haystack:
            violations.append(
                f"{symbol}: the consumer the ledger names is not using it in "
                f"{live_path}"
            )
    assert not violations, f"KEEP ledger gaps: {violations}"


# ---------------------------------------------------------------------------
# AC-D65.1 re-run on the finished tree — the dock measurable, over tests/
# ---------------------------------------------------------------------------

#: The token tables, which must be able to spell the retired title.
DOCK_CARVE_OUT = ("tests/test_d45_removal.py", "tests/test_d65_residue.py")
_DOCK_KEY_RE = re.compile(
    r"windowTitle|objectName|findChild|findChildren|setTitleBarWidget"
    r"|horizontalDockTitles|dock_title"
)
_TITLE_LOOKUP_RE = re.compile(
    r"(for [^\n]*windowTitle\(\)[^\n]* if|next\([^\n]*windowTitle"
    r"|filter\([^\n]*windowTitle|findChild(?:ren)?\([^\n]*windowTitle)"
)


def test_no_portfolio_dock_title_or_object_name_remains():
    violations = []
    for rel, text in sources().items():
        if rel in DOCK_CARVE_OUT:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "Portfolio" not in line or _negative_assertion(line):
                continue
            if _DOCK_KEY_RE.search(line):
                violations.append(f"{rel}:{lineno}: {line.strip()}")
    assert not violations, f"Portfolio dock keys survive: {violations}"


def test_no_title_keyed_right_dock_lookup_remains():
    violations = []
    for rel, text in sources().items():
        if not rel.startswith(TEST_DIR + "/") or rel in DOCK_CARVE_OUT:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _TITLE_LOOKUP_RE.search(line):
                violations.append(f"{rel}:{lineno}: {line.strip()}")
    assert not violations, (
        "docks must be found by objectName(), not by window title: "
        f"{violations}"
    )


# ---------------------------------------------------------------------------
# The batch gate record (AC-D65.11) and the bookkeeping checks
# ---------------------------------------------------------------------------


def test_record_names_the_three_owner_authorised_edits():
    for phrase in (
        "The D41 title re-points",
        "A194's supersession",
        "A201's D18 launch-width amendment with its two re-baselines",
        "The three owner-authorised pre-P23 edits",
    ):
        assert phrase in GATE_RECORD, f"gate record does not name {phrase!r}"


def test_record_names_the_s_p23_24_consequence():
    for phrase in (
        "S-P23-24",
        "D26.5's paper/live badge derivation retired with the account path",
        "account-typed inputs died with the account plane in",
        "the port guard proves the port alone",
        "● Connected",
        "edits no\n    requirements.md text",
    ):
        assert phrase in GATE_RECORD, f"gate record does not state {phrase!r}"


def test_record_declares_ac_d65_19_open_and_owned():
    assert "AC-D65.19" in GATE_RECORD
    assert "still OPEN" in GATE_RECORD
    assert "owned\n    by P23-T14" in GATE_RECORD, (
        "the record must name P23-T14 as AC-D65.19's owner"
    )
    assert "NOT claimed" in GATE_RECORD


def test_requirements_history_marker_and_sections_hold():
    text = _text("docs/requirements/requirements.md")
    assert "This is an existing repository." in text, "marker sentence gone"
    missing = [f"### D{n}" for n in range(41, 61) if f"### D{n}" not in text]
    assert not missing, f"missing D41–D60 sections: {missing}"
    # D61–D64 are recorded as one combined P22 section (its own structure —
    # there is no `### D61` heading to find). Their presence is measured by the
    # ACs the section carries.
    missing_ac = [
        f"AC-D{n}.1" for n in range(61, 65) if f"AC-D{n}.1" not in text
    ]
    assert not missing_ac, f"D61–D64 missing their ACs: {missing_ac}"


def test_conftest_names_no_dropped_table():
    text = _text("tests/conftest.py")
    for table in ("position_group_map", "trade_groups", "positions"):
        assert table not in text, (
            f"tests/conftest.py still wipes the dropped table {table!r}"
        )


def test_p13_allowlist_holds_the_option_panel_only():
    text = _text("tests/test_p13_gate.py")
    assert "option_spreads_panel.py" in text, (
        "the p13 allowlist lost the Option Spreads panel"
    )
    assert "active_portfolio_panel.py" not in text, (
        "the p13 allowlist still names the deleted Portfolio panel"
    )


def test_d45_suite_tests_no_deleted_subject():
    tree = ast.parse(_text("tests/test_d45_removal.py"))
    deleted_stems = (
        "news", "digest", "sltp", "stop_loss_target", "kill_switch",
        "order_builder", "strategy_detection", "portfolio_panel",
        "account_summary", "trade_group", "position_update",
    )
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("test_"):
                continue
            for stem in deleted_stems:
                if stem in node.name:
                    offenders.append(f"{node.name} ({stem})")
    assert not offenders, (
        f"tests/test_d45_removal.py still tests a deleted subject: {offenders}"
    )


# ---------------------------------------------------------------------------
# The consistency re-check (AC-D65.4/.6/.2/.3)
# ---------------------------------------------------------------------------

_CAP_RE = re.compile(r"(?:≤|<=)?\s*(\d+)\s*option\s*(?:lines?|slots?)")
_TOTAL_RES = (
    re.compile(r"(\d+)\s*option\s*(?:lines?|slots?)[^\n]{0,80}?(\d+)\s*total"),
    re.compile(r"(\d+)\s*option\s*\+\s*(?:1|one)\s*spot\s*=\s*(\d+)"),
    re.compile(r"(\d+)\s*\+\s*1\s*=\s*(\d+)"),
    re.compile(r"max\(option \+ spot[^\n]*?<=\s*(\d+)\)"),
    re.compile(r"max\(option for[^\n]*?<=\s*(\d+)\)"),
)
_BAND_RE = re.compile(r"max\(0\.05,\s*([A-Za-z_][\w.]*)\)")
#: A *spread* pair is only ever written as an instrument name. Every other
#: `NNNN/NNNN` in these files is adjacent legs in a window list (a legal 5-wide
#: gap) or a line range in prose, which is why the width rule is scoped to the
#: name shape rather than to any four digits either side of a slash.
_NAMED_PAIR_RE = re.compile(r"SPX\s+[A-Za-z0-9]+\s+(\d{4})/(\d{4})")
_PAIR_RE = re.compile(r"(?<!\d)(\d{4})/(\d{4})(?!\d)")


def test_option_line_counts_are_stated_identically():
    violations = []
    claimed = 0
    for rel in CONSISTENCY_FILES:
        text = _text(rel)
        for match in _CAP_RE.finditer(text):
            claimed += 1
            if int(match.group(1)) != OPTION_CAP:
                violations.append(f"{rel}: option cap {match.group(1)}")
        for pattern in _TOTAL_RES:
            for match in pattern.finditer(text):
                claimed += 1
                values = {int(g) for g in match.groups() if g is not None}
                if values not in ({OPTION_CAP, SPOT_TOTAL}, {SPOT_TOTAL}):
                    violations.append(f"{rel}: claim {sorted(values)}")
    assert not violations, f"line-count drift: {violations}"
    assert claimed >= 8, f"only {claimed} line-count claims found — too few"


def test_band_formula_is_stated_identically():
    violations = []
    files_with_band = set()
    for rel in CONSISTENCY_FILES:
        text = _text(rel)
        for match in _BAND_RE.finditer(text):
            files_with_band.add(rel)
            argument = match.group(1)
            if argument not in ("one_tick", "tick", "option_tick"):
                violations.append(f"{rel}: max(0.05, {argument})")
    assert not violations, f"band formula drift: {violations}"
    for required in ("docs/plan.md", "docs/architecture.md",
                     "tests/test_d65_option_ladder.py"):
        assert required in files_with_band, (
            f"{required} no longer states the tick-derived band"
        )


def test_credit_and_displayed_sign_pair_is_stated_identically():
    for rel in ("docs/plan.md", "docs/architecture.md",
                "tests/test_d65_option_ladder.py"):
        text = _text(rel)
        assert "credit_bid" in text and "credit_ask" in text, (
            f"{rel}: the credit bases are not both named"
        )
        assert re.search(r"ASK[^\n]{0,60}credit_bid|credit_bid[^\n]{0,60}ASK", text), (
            f"{rel}: the ASK-cell/credit_bid pairing is not stated"
        )
        assert re.search(r"[−-]credit_bid|[−-]display_ask", text), (
            f"{rel}: the displayed value is not stated as the credit's negative"
        )


def test_canonical_fixtures_survive_and_the_typos_do_not():
    files_with_fixtures = set()
    violations = []
    for rel in CONSISTENCY_FILES:
        lines = _text(rel).splitlines()
        text = "\n".join(lines)
        for fixture in CANONICAL_FIXTURES:
            if fixture in text:
                files_with_fixtures.add((rel, fixture))
        for lineno, line in enumerate(lines, start=1):
            window = " ".join(lines[max(0, lineno - 3):lineno]).lower()
            ban_context = any(marker in window for marker in _CLAIM_MARKERS)
            for match in _NAMED_PAIR_RE.finditer(line):
                short, long = int(match.group(1)), int(match.group(2))
                if abs(short - long) != 20 and not ban_context:
                    violations.append(
                        f"{rel}:{lineno}: named pair {short}/{long} is not 20 wide"
                    )
            for match in _PAIR_RE.finditer(line):
                short, long = int(match.group(1)), int(match.group(2))
                pair = f"{short}/{long}"
                if pair in BANNED_EXAMPLES and not ban_context:
                    violations.append(
                        f"{rel}:{lineno}: banned example {pair} presented live"
                    )
    for fixture in CANONICAL_FIXTURES:
        holders = {rel for rel, name in files_with_fixtures if name == fixture}
        for required in ("docs/plan.md", "docs/architecture.md",
                         "tests/test_d65_option_ladder.py",
                         "tests/test_d65_option_panel.py"):
            assert required in holders, (
                f"{required} no longer states the canonical fixture {fixture}"
            )
    # `7435/7455` is AC-D65.9(i)'s **legal** 20-wide pair and the ladder suite
    # exercises it in the comma form (`validate_spread("CCS", 7435, 7455)`);
    # only A212's two typos are banned. Guard the ban list itself so a later
    # tidy cannot widen it to a legal pair.
    assert LEGAL_NON_BANNED_PAIR not in BANNED_EXAMPLES
    assert not violations, f"fixture drift: {violations}"


def test_no_flat_band_phrasing_survives():
    violations = []
    for rel in CONSISTENCY_FILES:
        for lineno, line in enumerate(_text(rel).splitlines(), start=1):
            if "0.05" not in line:
                continue
            lowered = line.lower()
            if "band" not in lowered and "tolerance" not in lowered:
                continue
            if "max(0.05" in lowered:
                continue
            if any(marker in lowered for marker in _CLAIM_MARKERS):
                continue
            violations.append(f"{rel}:{lineno}: {line.strip()}")
    assert not violations, f"flat-0.05 band phrasing survives: {violations}"


# ---------------------------------------------------------------------------
# usage.md — the user-facing doc describes the panel that exists (AC-D65.5)
# ---------------------------------------------------------------------------


def test_usage_describes_the_option_spreads_panel():
    text = _text("usage.md")
    assert "Option Spreads" in text, "usage.md never names the panel"
    for claim in ("0.05", "19.95", "ON/OFF", "display-only", "no order entry"):
        assert claim in text, f"usage.md does not state {claim!r}"
    for stale in ("auto-detected by option strategy", "account summary, positions"):
        assert stale not in text, f"usage.md still claims {stale!r}"


def test_no_user_facing_doc_advertises_a_portfolio_view():
    violations = []
    for rel in ("usage.md", "USAGE.txt"):
        text = _text(rel)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "Portfolio" not in line or _negative_assertion(line):
                continue
            violations.append(f"{rel}:{lineno}: {line.strip()}")
    assert not violations, f"a user-facing doc still claims a Portfolio view: {violations}"
