"""P23-T13 — the standing Unused-Code Rule gate (S-P23-15) and the D65 batch gate.

Two instruments in one suite, because "nothing unused remains" can fail in two
different places and each needs its own net:

1. **The standing gate's five clauses** (``AC-D65.12``), run over the finished
   P23 tree *and* re-run over a seeded fixture so the gate is proven capable of
   going red before anyone trusts it green:

   (i)   every P23 symbol has a production caller or a cited **code**
         registration site (a document mention never counts). The candidate
         set is every public module-level name the four P23 modules offer
         **and** every method of every P23 class — sync and async, the
         ``@property``/``@staticmethod``/``@classmethod`` accessors included —
         each method keyed ``Class.method`` so it can never be confused with a
         module-level name of the same spelling. Clause (i)'s evidence is
         **production-only**: a reference only counts as a production caller
         when it lives outside ``tests/`` — in ``ui/``, ``services/``,
         ``data/``, ``ibkr/``, ``config/`` or ``main.py`` — while clause (ii)'s
         helper scan and clause (iii)'s token/import sweeps keep the full tree.
         A method key is additionally **class-bound** at both ends: its
         evidence must resolve to the declaring class's own member — a
         ``Class.method`` attribute access, a name/alias/attribute bound to
         ``Class(...)``, an annotated parameter, or ``self.method`` /
         ``cls.method`` inside the declaring class — never a bare name, a
         string constant, an argument name or an unrelated object's same-named
         attribute. Two exclusions exist and no others: a name that begins and
         ends with ``__`` (a dunder, Python's own protocol hook) is not
         censused, and a clause-(v) framework callback is exempt only through
         the cited declaring-class / registering-base entry below, consulted
         independently of reachability — and the clause-(i) allowlist itself is
         held per entry: the key must be one the census would otherwise report,
         it must have no *production* Python call site, and its citation must
         resolve — never a whole-dict literal, and never anything that forbids
         a legitimate exemption the phase's snapshot does not have yet;
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
   consequence and the still-open live-TWS criterion.

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

from PyQt6.QtWidgets import QStyledItemDelegate, QWidget

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
        "select_zero_dte_series",
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

#: Clause (i)'s exemption: a symbol that only framework machinery invokes *by
#: name*, so no production Python call site exists for the census to find. Every
#: value is the citation, and every citation must be a **code** registration
#: site of the exact shape ``"<repo-relative .py>:<line> — <how it is
#: invoked>"`` — ``test_census_allowlist_cites_a_live_site`` re-checks that the
#: cited line really invokes or registers the symbol by name (a call argument, a
#: ``connect``/``emit``, a name-keyed registry entry, or a base class).
#:
#: A *document* mention is never a site: ``docs/tasks/task-graph.json`` naming a
#: class in a task signature registers nothing, so it cannot keep a symbol
#: "live". A symbol kept only because a planning document names it is exactly
#: the keep-for-later residue clause (iii) forbids (ESC-118), and the allowlist
#: must never exist for that purpose.
#:
#: The mapping's safety property is asserted **per entry**, never as a literal of
#: the whole dict (ESC-122): ``scan_census_allowlist`` holds every entry to all
#: three halves at once — the key is one ``scan_unreferenced_symbols`` would
#: otherwise report, no *production* Python call site invokes the symbol, and the
#: citation resolves to a live registration site. An empty mapping therefore
#: passes trivially, and a legitimate entry (a duck-typed surface, or a callback
#: whose only caller is a name-keyed registration) can be added later without
#: rewriting an assertion that forbids every exemption.
#:
#: Phase-initial snapshot, not a rule: P23 closed with this mapping empty — no
#: P23 symbol needed the exemption, because the EWrapper/Qt callbacks have their
#: own clause-(v) tables below. That zero-exemption state is recorded as its own
#: phase-scoped assertion in the method-census case below; the standing
#: invariant above is what decides whether an entry is earned, so adding one
#: updates the snapshot rather than failing the rule.
CENSUS_ALLOWLIST: dict[str, dict[str, str]] = {}

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
#: virtual slots, not from Python. The key names the **declaring class** and the
#: method; the value is the **registering base class**. The census verifies that
#: the declaring class really inherits that base and that the base declares the
#: name, which is the registration site a Python call site cannot supply.
#:
#: The entry is scoped per (module, declaring class, method, registering base):
#: the same method name on another class, or under another base, is still
#: censused. A document mention is not a base class, so it exempts nothing —
#: the clause-(i) citation check below requires a live .py site for the same
#: reason.
FRAMEWORK_CALLBACKS: dict[tuple[str, str, str], type] = {
    ("ui/option_spreads_panel.py", "_ElideNameDelegate", "initStyleOption"):
        QStyledItemDelegate,
    # OptionSpreadsPanel subclasses QWidget directly, so QWidget — not the
    # delegate's base — is the class whose attribute registers sizeHint for it.
    ("ui/option_spreads_panel.py", "OptionSpreadsPanel", "sizeHint"):
        QWidget,
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
    # Its AC5 case proves the four deleted bridge signals absent, so it must
    # spell `account_summary`, `account_summary_end`, `position_update` and
    # `position_end`; no positive-polarity mention survives there.
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
    AC-D65.19 (the owner's live-TWS, read-only acceptance run) is still OPEN and
    is owned by P23-T26. The build can observe every other AC-D65.* criterion; it
    cannot observe a live TWS session, and this record claims exactly that. The
    run is read-only by construction — the panel issues only reqSecDefOptParams,
    reqMktData and cancelMktData — and no checklist item asks the owner to place,
    modify or cancel an order.
"""

# ---------------------------------------------------------------------------
# loading + the pure scanners
# ---------------------------------------------------------------------------

_SOURCE_CACHE: dict[str, str] | None = None


def _text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def sources() -> dict[str, str]:
    """Every Python source the gate measures, keyed by repo-relative path.

    Clause (ii)'s helper scan and clause (iii)'s token/import sweeps read this
    full map (production directories, ``main.py`` and ``tests/``). Clause (i)'s
    reachability is narrower by construction: ``_production_subset`` drops every
    path whose first segment is ``tests``, so a test-only reference is never a
    production caller.
    """
    global _SOURCE_CACHE
    if _SOURCE_CACHE is None:
        out: dict[str, str] = {}
        for directory in (*SOURCE_DIRS, TEST_DIR):
            for path in sorted((REPO / directory).rglob("*.py")):
                out[path.relative_to(REPO).as_posix()] = path.read_text(
                    encoding="utf-8"
                )
        entry_point = REPO / "main.py"
        if entry_point.is_file():
            out["main.py"] = entry_point.read_text(encoding="utf-8")
        _SOURCE_CACHE = out
    return _SOURCE_CACHE


def _production_subset(tree: dict[str, str]) -> dict[str, str]:
    """Clause (i)'s reachability pool: every path that is not under ``tests/``.

    That is ``ui/``, ``services/``, ``data/``, ``ibkr/``, ``config/`` and the
    ``main.py`` entry point in the real tree, and every non-test module in a
    fixture tree. Clause (ii) and clause (iii) keep scanning the full tree.
    """
    return {
        path: text
        for path, text in tree.items()
        if path.split("/")[0] != TEST_DIR
    }


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


def _module_definitions(text: str) -> set[str]:
    """Every name a module defines: its top-level names and its class members.

    An inventory entry is only evidence of a live symbol when the module really
    defines it — a module-level ``def``/``class``/constant or a member of a
    class defined there. A name that only *mentions* itself somewhere is not a
    definition, which is what lets a deleted symbol's stale entry fail.
    """
    module = ast.parse(text)
    defined: set[str] = set()

    def add_targets(target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            defined.add(target.id)

    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                add_targets(target)
        elif isinstance(node, ast.AnnAssign):
            add_targets(node.target)
    for node in ast.walk(module):
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(child.name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    add_targets(target)
            elif isinstance(child, ast.AnnAssign):
                add_targets(child.target)
    return defined


def _inventory_gaps(
    tree: dict[str, str], inventory: dict[str, tuple[str, ...]]
) -> list[str]:
    """``module:name`` for every inventory entry its module does not define."""
    gaps: list[str] = []
    for module, names in inventory.items():
        text = tree.get(module)
        if text is None:
            gaps.append(f"{module}: (module is not scanned)")
            continue
        defined = _module_definitions(text)
        gaps.extend(f"{module}:{name}" for name in names if name not in defined)
    return gaps


def _class_methods(
    text: str, class_names: set[str] | None = None
) -> tuple[str, ...]:
    """``Class.method`` for every method the module's classes define.

    Decorated accessors are ordinary ``FunctionDef`` nodes, so
    ``@property``/``@staticmethod``/``@classmethod`` methods are included. The
    one exclusion is a dunder name (``__x__``): Python invokes those through the
    protocol, never through a call site of ours. A method key carries its
    declaring class, so it cannot collide with a module-level name of the same
    spelling. Getter/setter pairs collapse onto one key.
    """
    names: list[str] = []
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.ClassDef):
            continue
        if class_names is not None and node.name not in class_names:
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if child.name.startswith("__") and child.name.endswith("__"):
                continue
            names.append(f"{node.name}.{child.name}")
    return tuple(dict.fromkeys(names))


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


def _class_node(text: str, class_name: str) -> ast.ClassDef | None:
    """The ``ClassDef`` named ``class_name`` in ``text``, or None."""
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def _base_names(node: ast.ClassDef) -> set[str]:
    """The last name of every declared base (``Qt.X`` counts as ``X``)."""
    names: set[str] = set()
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _annotation_name(node: ast.AST | None) -> str | None:
    """The class an annotation names, for ``X: Class`` / ``X: Optional[Class]``."""
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Subscript):
        wrapper = _annotation_name(node.value)
        if wrapper in ("Optional", "Union"):
            return _annotation_name(node.slice)
    return None


def _base_key(node: ast.AST) -> str | None:
    """A textual key for an expression used as an attribute base.

    ``engine`` -> ``"engine"``; ``self.engine`` -> ``"self.engine"``;
    ``SpreadEngine()`` -> ``"SpreadEngine"`` (its constructor names the class).
    Anything else (a call result, a subscript, arithmetic) keys to ``None``,
    so it can never resolve as an instance of a class.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _base_key(node.value)
        return f"{prefix}.{node.attr}" if prefix else None
    if isinstance(node, ast.Call):
        return _base_key(node.func)
    return None


def _class_bound_names(text: str, class_name: str) -> set[str]:
    """Expression keys in ``text`` that hold the class or one of its instances.

    The class name itself is always a valid base (``Class.method``). Names,
    annotated parameters and attribute targets then join the set by assignment
    (``name = Class(...)``, ``self.attr = Class(...)``) or by annotation
    (``engine: Class``, ``self.attr: Class``), and the fixed point follows
    aliases (``panel = self.option_spreads_panel``), so an access through a name
    or an attribute bound to an instance resolves — and a same-named attribute
    on an unrelated object does not.
    """
    bound: set[str] = {class_name}
    nodes = list(ast.walk(ast.parse(text)))
    changed = True
    while changed:
        changed = False
        for node in nodes:
            if isinstance(node, ast.arg):
                key = node.arg
                if _annotation_name(node.annotation) == class_name and key not in bound:
                    bound.add(key)
                    changed = True
            elif isinstance(node, ast.AnnAssign):
                if _annotation_name(node.annotation) == class_name:
                    key = _base_key(node.target)
                    if key and key not in bound:
                        bound.add(key)
                        changed = True
            elif isinstance(node, ast.Assign):
                if _base_key(node.value) not in bound:
                    continue
                for target in node.targets:
                    key = _base_key(target)
                    if key and key not in bound:
                        bound.add(key)
                        changed = True
    return bound


def _method_evidence(
    tree: dict[str, str], module: str, declaring_class: str, method: str
) -> bool:
    """True when some file references ``declaring_class.method`` class-bound.

    Two shapes count, and only these:

    * an attribute access ``<base>.method`` whose base resolves through
      ``_class_bound_names`` to the declaring class (the class itself, an
      instance it constructs, an annotated parameter, an alias, or an
      attribute holding one); and
    * ``self.method`` / ``cls.method`` inside the declaring class body — the
      method's own receiver, which no external binding can express.

    A bare name, a string constant, a function argument name that is not
    annotated with the class, and a same-named attribute on an unrelated
    object's instance are therefore not evidence.
    """
    for text in tree.values():
        bounds = _class_bound_names(text, declaring_class)
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Attribute) and node.attr == method:
                if _base_key(node.value) in bounds:
                    return True
    class_node = _class_node(tree.get(module, ""), declaring_class)
    if class_node is not None:
        for node in ast.walk(class_node):
            if not isinstance(node, ast.Attribute) or node.attr != method:
                continue
            receiver = node.value
            if isinstance(receiver, ast.Name) and receiver.id in ("self", "cls"):
                return True
    return False


def _framework_callback_exempt(
    module: str,
    declaring_class: str,
    method: str,
    entries: dict[tuple[str, str, str], object],
    tree: dict[str, str],
) -> bool:
    """True only for a validating (declaring class, registering base) entry.

    The entry exempts a method only when its value is a class, that class
    declares ``method``, the declaring class really inherits it, and the class
    body defines the method. A document string is not a class, so it exempts
    nothing.
    """
    base = entries.get((module, declaring_class, method))
    if not isinstance(base, type) or not hasattr(base, method):
        return False
    text = tree.get(module)
    if text is None:
        return False
    class_node = _class_node(text, declaring_class)
    if class_node is None or base.__name__ not in _base_names(class_node):
        return False
    return any(
        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and child.name == method
        for child in class_node.body
    )


def scan_unreferenced_symbols(
    tree: dict[str, str],
    candidates: dict[str, tuple[str, ...]],
    allowlist: dict[str, dict[str, str]] | None = None,
    framework_callbacks: dict[tuple[str, str, str], object] | None = None,
    reachability_tree: dict[str, str] | None = None,
) -> list[str]:
    """Clause (i): `module:symbol` for every candidate nothing references.

    Reachability is **production-only**: ``reachability_tree`` defaults to the
    production subset of ``tree`` (``_production_subset`` — every path whose
    first segment is not ``tests``), so a reference that exists only in a test
    file is never a production caller. Clause (ii)'s helper scan and clause
    (iii)'s token/import sweeps are untouched; they keep reading the full tree.

    A module-level name is evidenced by a load/attribute/import mention inside
    its own module beyond the definition or in another *production* file. A
    ``Class.method`` key is evidenced only **class-bound** at both ends: an
    attribute access on the declaring class itself, on a name/alias/attribute
    bound to ``Class(...)`` (an annotated parameter included), or
    ``self.method`` / ``cls.method`` inside the declaring class — never a bare
    name, a string constant, an argument name or an unrelated object's
    same-named attribute.

    Two exclusions exist and no others. An allowlisted symbol needs a citation
    that resolves to a live code site. A **clause-(v) cited-base exemption** is
    the one other way out: it must name the (declaring class, registering base)
    entry, and the base must actually declare the method, so a same-named
    method on a class without that base is censused and reported; that check is
    consulted independently of reachability, after a failed reachability test.
    A document string satisfies neither, a method key is never satisfied by a
    module-level symbol of the same spelling, and dunder method names are never
    candidates (the dunder exclusion lives in ``_class_methods``).
    """
    allowlist = allowlist or {}
    framework_callbacks = framework_callbacks or {}
    reach = (
        _production_subset(tree)
        if reachability_tree is None
        else reachability_tree
    )
    used = {path: _load_names(text) for path, text in tree.items()}
    mentioned = {path: _mention_names(text) for path, text in reach.items()}
    violations: list[str] = []
    for module, symbols in candidates.items():
        for symbol in symbols:
            citation = allowlist.get(module, {}).get(symbol)
            if citation is not None and citation_violation(
                module, symbol, citation, tree
            ) is None:
                continue
            if "." in symbol:
                declaring_class, method = symbol.rsplit(".", 1)
            else:
                declaring_class, method = "", symbol
            probe = method
            if declaring_class:
                if _method_evidence(reach, module, declaring_class, method):
                    continue
            else:
                if probe in used.get(module, set()):
                    continue
                if any(
                    probe in mentioned[path]
                    for path in reach
                    if path != module
                ):
                    continue
            if declaring_class and _framework_callback_exempt(
                module, declaring_class, method, framework_callbacks, tree
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
    """The clause-(i) candidate map: module-level names and ``Class.method``.

    The four P23 modules contribute their public top-level names plus every
    method of every class they define; a module P23 extended contributes the
    explicitly listed symbols plus the methods of any class among them.

    Both halves are judged against a **production-only** reachability pool: a
    reference from a file under ``tests/`` is not a production caller (clause
    (ii)'s helper scan and clause (iii)'s sweeps still read the full tree). A
    ``Class.method`` key is additionally **class-bound** at both ends — its
    evidence must be an attribute access on the declaring class itself or on a
    name/alias/attribute bound to ``Class(...)`` (an annotated parameter
    included), or ``self.method`` / ``cls.method`` inside the declaring class —
    never a bare name, a string constant, an argument name or an unrelated
    object's same-named attribute. The only exclusions are the dunder exclusion
    (a ``__x__`` protocol hook, see ``_class_methods``) and a clause-(v)
    framework callback cited with its (declaring class, registering base)
    entry.
    """
    candidates: dict[str, tuple[str, ...]] = {}
    for module in P23_NEW_MODULES:
        candidates[module] = (
            _defined_symbols(tree[module]) + _class_methods(tree[module])
        )
    for module, extra in P23_ADDED_SYMBOLS.items():
        candidates[module] = (
            tuple(candidates.get(module, ()))
            + extra
            + _class_methods(tree[module], set(extra))
        )
    return candidates


def test_every_p23_symbol_has_a_caller_or_a_cited_registration_site():
    tree = sources()
    violations = scan_unreferenced_symbols(
        tree, _census_candidates(tree), CENSUS_ALLOWLIST, FRAMEWORK_CALLBACKS
    )
    assert not violations, (
        "P23 symbols with no caller and no cited registration site: "
        f"{violations}"
    )


def test_method_census_covers_p23_classes_and_excludes_dunders():
    """AC1: every P23 class method is a ``Class.method`` candidate; dunders are not."""
    tree = sources()
    candidates = _census_candidates(tree)
    engine = candidates["services/option_spread_engine.py"]
    for key in (
        "SpreadEngine.toggle_off",
        "SpreadEngine.reset_session",
        # The deleted ``SpreadEngine.target`` property's slot is held by two
        # members the class really defines today (ESC-121: the case must name
        # real members, not whatever happens to pass).
        "SpreadEngine.set_target",
        "SpreadEngine.band",
    ):
        assert key in engine, f"{key} missing from the method census"
    for absent in (
        # The property P23 deleted; a census that re-adopts it would be stale.
        "SpreadEngine.target",
        # A dunder is the one exclusion and a synthetic non-member never was a
        # candidate, so both negatives keep the case discriminating.
        "SpreadEngine.__init__",
        "SpreadEngine.not_a_method",
    ):
        assert absent not in engine, f"{absent} must not be in the method census"
    panel = candidates["ui/option_spreads_panel.py"]
    for key in (
        "OptionSpreadsPanel._cells_for",
        "OptionSpreadsPanel._table_item",
    ):
        assert key in panel, f"{key} missing from the method census"
    for module in P23_NEW_MODULES:
        for node in ast.walk(ast.parse(tree[module])):
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                key = f"{node.name}.{child.name}"
                dunder = child.name.startswith("__") and child.name.endswith("__")
                assert (key in candidates[module]) is not dunder, (
                    f"{module}:{key} must be censused unless it is a dunder"
                )
    backup = _class_node(tree["data/db_backup.py"], "VerifiedBackupPath")
    assert backup is not None, "VerifiedBackupPath is gone from data/db_backup.py"
    assert any(child.name == "__new__" for child in backup.body if isinstance(
        child, (ast.FunctionDef, ast.AsyncFunctionDef)
    )), "the fixture's dunder exclusion subject is gone"
    assert "VerifiedBackupPath.__new__" not in candidates["data/db_backup.py"], (
        "a dunder is the one exclusion and must not be censused"
    )
    # The standing invariant (ESC-122): each entry earns itself against the
    # same census it stands beside — the key is one the scanner would otherwise
    # report, no production call site invokes it, and its citation resolves to
    # a live registration site. Never a whole-dict literal: that form would
    # forbid a legitimate exemption along with the unsafe ones and would make
    # its own message wrong for one.
    problems = scan_census_allowlist(tree, candidates=candidates)
    assert not problems, (
        "a census exemption must earn itself (a key the scanner would "
        "otherwise report, no production call site, a resolving registration "
        f"citation): {problems}"
    )
    # Phase snapshot (ESC-122), recorded separately and phase-scoped — NEVER
    # the standing rule. P23 closed with no exemption needed; if a symbol needs
    # one later, the entry above is what decides whether it is earned, and this
    # snapshot is updated with it rather than forbidding it.
    assert not CENSUS_ALLOWLIST, (
        "P23 phase snapshot (phase-scoped, not the standing rule): no P23 "
        "symbol needs a census exemption today. If one does, cite it and "
        "update this snapshot; scan_census_allowlist decides whether the "
        "entry is earned."
    )
    assert scan_unreferenced_symbols(
        tree, candidates, CENSUS_ALLOWLIST, FRAMEWORK_CALLBACKS
    ) == []
    # Composed, never spelled literally: the searched name would otherwise
    # occur in this assertion's own source line and message and could never
    # pass. The gate's candidate list and prose must not name the helper
    # P23-T20 deleted.
    stale_helper = "validate" + "_spread"
    assert stale_helper not in _text("tests/test_d65_residue.py"), (
        f"the gate still names {stale_helper}, which P23-T20 deleted"
    )


def test_docstring_states_the_implemented_census_scope():
    """AC5: production-only evidence, class-bound methods, two exclusions."""
    module = ast.parse(_text("tests/test_d65_residue.py"))
    module_doc = ast.get_docstring(module) or ""
    bullet = re.search(r"\(i\)\s+(.*?)\n\s{0,6}\(ii\)", module_doc, re.S)
    assert bullet is not None, "the module docstring lost its clause-(i) bullet"
    claim = bullet.group(1)
    assert "method" in claim.lower(), "clause (i) does not name class methods"
    assert "production-only" in claim.lower(), (
        "clause (i) does not state that its reachability evidence is "
        "production-only"
    )
    assert "class-bound" in claim.lower(), (
        "clause (i) does not state that a method's evidence is class-bound"
    )
    assert "dunder" in claim.lower(), "clause (i) does not name the dunder exclusion"
    assert re.search(r"clause-?\(v\)", claim), (
        "clause (i) does not name the clause-(v) cited-site exemption"
    )
    assert "independently of reachability" in claim.lower(), (
        "clause (i) does not state that the framework exemption is consulted "
        "independently of reachability"
    )
    for narrow in (
        "module-level names only",
        "module-level only",
        "top-level names only",
        "only module-level",
        "only top-level",
        "bare-name",
        "bare name counts",
    ):
        assert narrow not in module_doc.lower(), f"stale scope claim: {narrow!r}"
    functions = {
        node.name: ast.get_docstring(node) or ""
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for name in (
        "_class_methods", "_census_candidates", "scan_unreferenced_symbols",
    ):
        assert "method" in functions[name].lower(), (
            f"{name}'s docstring does not describe the method census"
        )
    for name in ("_census_candidates", "scan_unreferenced_symbols"):
        doc = functions[name]
        assert "production-only" in doc.lower(), (
            f"{name} does not state that clause (i)'s evidence is production-only"
        )
        assert "class-bound" in doc.lower(), (
            f"{name} does not state that a method's evidence is class-bound"
        )
        assert "dunder" in doc.lower(), (
            f"{name} does not name the dunder exclusion"
        )
        assert re.search(r"clause-?\(v\)", doc), (
            f"{name} does not name the clause-(v) cited-base exemption"
        )
        assert "bare-name" not in doc.lower(), (
            f"{name} still carries the old bare-name claim"
        )
    assert "dunder" in functions["_class_methods"].lower(), (
        "_class_methods does not name the dunder exclusion"
    )
    assert "Class.method" in functions["_census_candidates"], (
        "_census_candidates does not state the method key shape"
    )
    candidates = _census_candidates(sources())
    assert "SpreadEngine.reset_session" in candidates["services/option_spread_engine.py"], (
        "a docstring method claim is not backed by the candidate map"
    )
    assert not any(
        key.endswith(".__new__") for key in candidates["data/db_backup.py"]
    ), "the docstring's dunder exclusion is not backed by the candidate map"


def test_p23_added_symbols_resolve_to_real_definitions():
    """AC6: every inventory entry names a symbol the module still defines."""
    tree = sources()
    contracts = P23_ADDED_SYMBOLS["ibkr/contracts.py"]
    assert "option_chain_strikes" not in contracts, (
        "the inventory still files option_chain_strikes, which P23-T21 deleted "
        "from ibkr/contracts.py"
    )
    assert _inventory_gaps(
        tree, {"ibkr/contracts.py": ("option_chain_strikes",)}
    ) == ["ibkr/contracts.py:option_chain_strikes"], (
        "the inventory check must report the deleted symbol, not accept its own "
        "self-mention"
    )
    assert not _inventory_gaps(tree, P23_ADDED_SYMBOLS), (
        "a P23_ADDED_SYMBOLS entry names a symbol its module no longer defines: "
        f"{_inventory_gaps(tree, P23_ADDED_SYMBOLS)}"
    )
    phantom = {
        module: tuple(names) + ("phantom_symbol",)
        for module, names in P23_ADDED_SYMBOLS.items()
    }
    gaps = _inventory_gaps(tree, phantom)
    assert len(gaps) == len(P23_ADDED_SYMBOLS) and all(
        gap.endswith(":phantom_symbol") for gap in gaps
    ), f"a seeded phantom inventory entry was not reported: {gaps}"


#: A citation must name a **Python** file, a line in it, and how the symbol is
#: invoked there. `docs/…json` and `docs/…md` cannot match the path group, so a
#: planning-document signature can never pass (ESC-118).
_REGISTRATION_RE = re.compile(
    r"^(?P<path>[A-Za-z0-9_./-]+\.py):(?P<line>\d+)\s*"
    r"(?:—|–|-{1,2})\s*(?P<how>\S.*)$"
)


def _invokes_by_name(source: str, symbol: str, lineno: int) -> bool:
    """True when the statement at ``lineno`` invokes/registers ``symbol``.

    ``symbol`` is a bare module-level name or a ``Class.method`` key; a method
    key is matched by its method name (the declaring-class check is
    ``citation_violation``'s). Three shapes count, and only these: the symbol
    passed as a call argument or keyword value (a signal ``connect``/``emit``, a
    dispatch-table insert, a callback handed to a framework), the symbol as a
    class base (a virtual-slot implementation), and the symbol as a **string
    constant** argument (a name-keyed registry such as ibapi's). A bare mention
    — an import, a docstring, the definition itself — registers nothing, which
    is what makes the citation evidence instead of prose.
    """
    probe = symbol.rpartition(".")[2] or symbol
    module = ast.parse(source)
    for node in ast.walk(module):
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None) or start
        if start is None or not (start <= lineno <= end):
            continue
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == probe:
                    return True
                if isinstance(base, ast.Attribute) and base.attr == probe:
                    return True
        if isinstance(node, ast.Call):
            for value in [*node.args, *(kw.value for kw in node.keywords)]:
                if isinstance(value, ast.Name) and value.id == probe:
                    return True
                if isinstance(value, ast.Attribute) and value.attr == probe:
                    return True
                if isinstance(value, ast.Constant) and value.value == probe:
                    return True
    return False


def _defines_symbol(module: str, symbol: str, tree: dict[str, str]) -> bool:
    """True when ``module`` still defines ``symbol`` (a method or a bare name)."""
    text = tree.get(module, "")
    if "." not in symbol:
        return symbol in text
    declaring_class, method = symbol.rsplit(".", 1)
    class_node = _class_node(text, declaring_class)
    return class_node is not None and any(
        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and child.name == method
        for child in class_node.body
    )


def citation_violation(
    module: str, symbol: str, citation: str, tree: dict[str, str]
) -> str | None:
    """Why ``citation`` fails to register ``symbol`` at a live code site, or None."""
    text = (citation or "").strip()
    if not text:
        return f"{module}:{symbol} has an empty citation"
    match = _REGISTRATION_RE.match(text)
    if match is None:
        return (
            f"{module}:{symbol} cites {citation!r}, which is not "
            "'<repo-relative .py>:<line> — <how it is invoked>'; a document "
            "mention registers nothing"
        )
    path, lineno = match.group("path"), int(match.group("line"))
    if path not in tree:
        return (
            f"{module}:{symbol} cites {path!r}, which is not a Python source the "
            "gate scans — only a code site can register a symbol"
        )
    if not 1 <= lineno <= len(tree[path].splitlines()):
        return f"{module}:{symbol} cites {path}:{lineno}, which is outside the file"
    if not _invokes_by_name(tree[path], symbol, lineno):
        return (
            f"{module}:{symbol} is cited at {path}:{lineno}, but that site does "
            "not invoke or register the symbol by name"
        )
    if not _defines_symbol(module, symbol, tree):
        return f"{module}:{symbol} is allowlisted but the module no longer defines it"
    return None


def _has_python_call_site(tree: dict[str, str], symbol: str) -> bool:
    """True when a *production* file calls ``symbol`` (``f(...)`` or ``x.f(...)``).

    The clause-(i) exemption exists for a symbol nothing in production Python
    calls — a registration site or the framework invokes it by name instead.
    The pool is ``_production_subset(tree)``, the same one the census judges
    reachability against: a reference that exists only under ``tests/`` is not a
    production caller (P23-T18), so a test exercising a name-invoked surface
    does not make its exemption amnesty.

    Naming the symbol as an argument, a base class or a string is a
    registration, not a call, so only an ``ast.Call`` whose callee carries the
    name counts here. The name is matched the way the census matches it: by the
    last component, so a ``Class.method`` key is probed by ``method``.
    """
    probe = symbol.rpartition(".")[2] or symbol
    for text in _production_subset(tree).values():
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            if isinstance(callee, ast.Name) and callee.id == probe:
                return True
            if isinstance(callee, ast.Attribute) and callee.attr == probe:
                return True
    return False


def _tree_candidates(tree: dict[str, str]) -> dict[str, tuple[str, ...]]:
    """A fixture tree's own census candidates: public names + ``Class.method``.

    The real tree passes ``_census_candidates`` (which knows the P23 inventory);
    a seeded fixture has no inventory, so its candidate set is what it defines.
    """
    return {
        module: _defined_symbols(text) + _class_methods(text)
        for module, text in tree.items()
    }


def scan_census_allowlist(
    tree: dict[str, str],
    allowlist: dict[str, dict[str, str]] | None = None,
    candidates: dict[str, tuple[str, ...]] | None = None,
    framework_callbacks: dict[tuple[str, str, str], object] | None = None,
) -> list[str]:
    """Clause (i)'s exemption property, checked per entry rather than per dict.

    Every entry must earn all three halves at once, and an empty mapping passes
    trivially — the property says nothing about how many exemptions exist:

    * **the scanner would otherwise report it** — ``scan_unreferenced_symbols``
      with no exemptions lists ``module:symbol``, so the entry covers a key the
      census really needs an answer for; an entry over a symbol production
      already references is dead weight, whatever its citation says;
    * **no production Python call site** — ``_has_python_call_site`` finds no
      ``f(...)`` or ``x.f(...)`` for the symbol in ``_production_subset(tree)``,
      so the entry covers only what a registration site can invoke by name; an
      entry over a symbol Python really calls is amnesty; and
    * **a cited registration site** — ``citation_violation`` resolves the
      citation to a live line that invokes or registers the symbol by name (a
      call argument, a ``connect``/``emit``, a name-keyed registry entry, a base
      class), which a document mention never does.

    A legitimate entry — a duck-typed surface, or a framework-invoked shape a
    clause-(v) base cannot express — passes all three; that is exactly the
    entry a whole-dict ``== {}`` assertion forbids and this check must allow
    (ESC-122).
    """
    allowlist = CENSUS_ALLOWLIST if allowlist is None else allowlist
    if candidates is None:
        candidates = _tree_candidates(tree)
    unexempted = set(
        scan_unreferenced_symbols(tree, candidates, {}, framework_callbacks)
    )
    problems: list[str] = []
    for module, entries in allowlist.items():
        for symbol, citation in entries.items():
            key = f"{module}:{symbol}"
            problem = citation_violation(module, symbol, citation, tree)
            if problem is not None:
                problems.append(problem)
                continue
            if symbol not in candidates.get(module, ()):
                problems.append(
                    f"{key} is allowlisted but is not a clause-(i) census "
                    "candidate; only a symbol the scanner would otherwise "
                    "report can be exempted"
                )
                continue
            if key not in unexempted:
                problems.append(
                    f"{key} is allowlisted but the scanner would not report "
                    "it: production already references the symbol, so no "
                    "exemption is needed"
                )
                continue
            if _has_python_call_site(tree, symbol):
                problems.append(
                    f"{key} is allowlisted but has a Python call "
                    "site; an exemption is for a symbol only a registration "
                    "site invokes by name"
                )
    return problems


def test_census_allowlist_cites_a_live_site():
    """No allowlist entry may be a bare name — each citation must resolve to code."""
    tree = sources()
    candidates = _census_candidates(tree)
    violations = []
    for module, entries in CENSUS_ALLOWLIST.items():
        if module not in candidates:
            violations.append(f"allowlist names an unscanned module: {module}")
            continue
        for symbol, citation in entries.items():
            problem = citation_violation(module, symbol, citation, tree)
            if problem:
                violations.append(problem)
    assert not violations, f"census allowlist is not evidence: {violations}"


def test_census_allowlist_rejects_a_document_mention():
    """ESC-118, proven red: a task-graph signature is not a registration site."""
    tree = {
        "sample.py": (
            "def handler(value):\n"
            "    return value\n"
            "\n"
            "\n"
            "class Owner:\n"
            "    def wire(self, signal):\n"
            "        signal.connect(handler)\n"
        ),
    }
    mentioned = (
        "docs/tasks/task-graph.json P23-T7 signature `class OptionSpreadEngine`"
    )
    assert citation_violation("sample.py", "handler", mentioned, tree), (
        "a document mention satisfied the allowlist"
    )
    assert citation_violation(
        "sample.py", "handler", "docs/plan.md:12 — named in the plan", tree
    ), "a non-Python citation satisfied the allowlist"
    assert citation_violation(
        "sample.py", "handler", "sample.py:1 — the definition itself", tree
    ), "a definition line must not count as a registration site"
    assert citation_violation(
        "sample.py", "handler", "sample.py:7 — signal connect", tree
    ) is None, "a real connect site was rejected"


def test_census_allowlist_entries_are_each_earned():
    """ESC-122: the property is per entry, so an empty mapping passes trivially.

    The seeded cases below are why this is not a whole-dict ``CENSUS_ALLOWLIST
    == {}`` literal: a literal of the whole dict forbids the legitimate entry
    (case a) along with the unsafe ones, so it makes an exemption impossible
    instead of proving one unsafe. Each entry is held to its own three halves:
    the key is one the scanner would otherwise report (case d is the negative),
    no production call site invokes it (case b), and the citation resolves to a
    registration site (case c).
    """
    tree = sources()
    candidates = _census_candidates(tree)
    # (0) An empty mapping over the real tree passes trivially: the invariant
    # says nothing about how many exemptions a phase needs. The phase's own
    # zero-exemption state is a separate, phase-scoped assertion elsewhere.
    assert scan_census_allowlist(tree, {}, candidates=candidates) == [], (
        "an empty allowlist must pass the per-entry invariant trivially"
    )
    problems = scan_census_allowlist(tree, candidates=candidates)
    assert not problems, (
        "census allowlist entries that do not earn their exemption: "
        f"{problems}"
    )
    fixture = {
        "fixture_module.py": (
            "class Owner:\n"
            "    def called(self):\n"
            "        return 1\n"
            "\n"
            "    def handler(self, value):\n"
            "        return value\n"
        ),
        "caller_module.py": (
            "def drive(owner):\n"
            "    return owner.called()\n"
            "\n"
            "\n"
            "def wire(owner, signal):\n"
            "    signal.connect(owner.handler)\n"
            "    signal.connect(owner.called)\n"
        ),
    }
    # (a) A handler registered at a real connect site: the legitimate entry
    # ESC-122 requires the gate to accept.
    legitimate = {
        "fixture_module.py": {
            "Owner.handler": "caller_module.py:6 — passed to signal.connect()"
        }
    }
    assert scan_census_allowlist(fixture, legitimate) == [], (
        "a name-invoked handler with a resolving connect-site citation must be "
        "allowlistable — the standing invariant is per entry, not 'no exemptions'"
    )
    # (b) The same citation shape, but for a method Python really calls: an
    # exemption may not stand in for a symbol that has a production call site.
    amnesty = {
        "fixture_module.py": {
            "Owner.called": "caller_module.py:7 — passed to signal.connect()"
        }
    }
    problems = scan_census_allowlist(fixture, amnesty)
    assert len(problems) == 1 and "Owner.called" in problems[0] and (
        "call site" in problems[0]
    ), f"a call site must be reported, not exempted: {problems}"
    # (c) A document mention satisfies none of the halves: no .py site resolves.
    documented = {
        "fixture_module.py": {
            "Owner.handler": (
                "docs/tasks/task-graph.json P23-T17 signature"
            )
        }
    }
    problems = scan_census_allowlist(fixture, documented)
    assert len(problems) == 1 and "document" in problems[0], (
        f"a document mention must exempt nothing: {problems}"
    )
    # (d) A well-cited entry for a symbol production already references: the
    # scanner would not report it, so the exemption is dead weight, not amnesty.
    redundant_tree = {
        "fixture_module.py": (
            "class Owner:\n"
            "    def swept(self):\n"
            "        return 3\n"
        ),
        "caller_module.py": (
            "def drive(owner: Owner):\n"
            "    return owner.swept()\n"
            "\n"
            "\n"
            "def wire(owner, signal):\n"
            "    signal.connect(owner.swept)\n"
        ),
    }
    redundant = {
        "fixture_module.py": {
            "Owner.swept": "caller_module.py:6 — passed to signal.connect()"
        }
    }
    problems = scan_census_allowlist(redundant_tree, redundant)
    assert len(problems) == 1 and "Owner.swept" in problems[0] and (
        "would not report" in problems[0]
    ), f"an exemption production does not need must be reported: {problems}"
    # (e) The legitimate entry and the empty mapping are the two shapes an
    # exemption can take; the phase snapshot that records "none today" is
    # asserted separately (``test_census_allowlist_state_is_phase_scoped``).
    assert scan_census_allowlist(fixture, {}, candidates=None) == [], (
        "a fixture tree with no exemptions must pass trivially too"
    )


def _compares_allowlist_to_empty_dict(node: ast.AST) -> bool:
    """True when ``node`` is a comparison between ``CENSUS_ALLOWLIST`` and ``{}``."""
    if not isinstance(node, ast.Compare):
        return False
    operands = [node.left, *node.comparators]
    has_allowlist = any(
        isinstance(op, ast.Name) and op.id == "CENSUS_ALLOWLIST" for op in operands
    )
    has_empty_dict = any(
        isinstance(op, ast.Dict) and not op.keys and not op.values
        for op in operands
    )
    return has_allowlist and has_empty_dict


def test_census_allowlist_state_is_phase_scoped_not_a_blanket_rule():
    """AC2 (ESC-122): the zero-exemption state is a snapshot, not the rule.

    Two claims about this suite, both read off its own AST: the wave-local
    whole-dict literal — ``CENSUS_ALLOWLIST == {}`` paired with the "no
    exemption may stand in for a symbol that has a call site" message — is
    gone, and the current zero-exemption state survives only as a separate,
    phase-scoped assertion whose message says no P23 symbol needs an exemption
    today and names itself as a snapshot rather than the standing invariant.
    """
    source = _text("tests/test_d65_residue.py")
    blanket_message = "no exemption may " + "stand in for"
    # The detector itself must be discriminating, or the absence check below
    # proves nothing: the banned form matches, the phase-scoped form does not.
    # The sample is composed so this file never spells the banned literal in a
    # form a grep could mistake for a live assertion.
    banned_sample = ast.parse(
        "assert CENSUS_ALLOWLIST " + "== {}, 'x'"
    ).body[0]
    phase_sample = ast.parse("assert not CENSUS_ALLOWLIST, 'x'").body[0]
    assert _compares_allowlist_to_empty_dict(banned_sample.test), (
        "the whole-dict detector misses the form it exists to ban"
    )
    assert not _compares_allowlist_to_empty_dict(phase_sample.test), (
        "the whole-dict detector would flag the phase-scoped snapshot"
    )
    whole_dict: list[str] = []
    phase_scoped: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assert):
            continue
        expression = ast.unparse(node.test)
        message = "" if node.msg is None else ast.unparse(node.msg)
        if _compares_allowlist_to_empty_dict(node.test):
            whole_dict.append(expression)
            assert blanket_message not in message, (
                "the suite still carries the blanket whole-dict assertion "
                f"({expression}) with its 'no exemption' message"
            )
        if (
            "CENSUS_ALLOWLIST" in expression
            and "phase-scoped" in message.lower()
            and "not the standing" in message.lower()
            and "no P23 symbol needs a census exemption today" in message
        ):
            assert blanket_message not in message, (
                "the phase-scoped snapshot still carries the prohibitive "
                "message it replaced"
            )
            phase_scoped.append(expression)
    assert not whole_dict, (
        "the suite still compares CENSUS_ALLOWLIST to an empty dict literal "
        f"({whole_dict}); the invariant is per entry, and the phase state is a "
        "separate snapshot"
    )
    assert len(phase_scoped) == 1, (
        "the phase's zero-exemption state is not recorded as exactly one "
        f"separate, phase-scoped assertion: {phase_scoped}"
    )
    assert "scan_census_allowlist" in source, (
        "the standing per-entry invariant is gone, leaving only the snapshot"
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
    tree = sources()
    for (module, declaring_class, method), base in FRAMEWORK_CALLBACKS.items():
        assert hasattr(base, method), (
            f"{module}:{declaring_class}.{method} is cited as a "
            f"{base.__name__} override, but the base class no longer declares it"
        )
        class_node = _class_node(tree[module], declaring_class)
        assert class_node is not None, (
            f"{module}:{declaring_class} is cited as the declaring class but "
            "is not defined there"
        )
        assert base.__name__ in _base_names(class_node), (
            f"{module}:{declaring_class} does not inherit {base.__name__}, so "
            f"the entry does not name {method}'s registration site"
        )
        assert any(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == method
            for child in class_node.body
        ), f"{module}:{declaring_class}.{method} is allowlisted but not defined"


def _framework_fixture_tree() -> dict[str, str]:
    """Two classes with the same name-invoked method, one under the Qt base."""
    return {
        "fixture_module.py": (
            "from PyQt6.QtWidgets import QStyledItemDelegate\n"
            "\n"
            "\n"
            "class Panel(QStyledItemDelegate):\n"
            "    def sizeHint(self, option, index):\n"
            "        return None\n"
            "\n"
            "\n"
            "class Plain:\n"
            "    def sizeHint(self, option, index):\n"
            "        return None\n"
        ),
    }


def test_framework_callback_exempt_only_through_declaring_class_and_base():
    """AC3: a cited (declaring class, registering base) entry and nothing less."""
    tree = _framework_fixture_tree()
    candidates = {"fixture_module.py": _class_methods(tree["fixture_module.py"])}
    unexempted = [
        "fixture_module.py:Panel.sizeHint",
        "fixture_module.py:Plain.sizeHint",
    ]
    assert scan_unreferenced_symbols(tree, candidates) == unexempted
    entry = {("fixture_module.py", "Panel", "sizeHint"): QStyledItemDelegate}
    assert scan_unreferenced_symbols(
        tree, candidates, framework_callbacks=entry
    ) == ["fixture_module.py:Plain.sizeHint"], (
        "the entry must exempt the class that inherits the registering base "
        "and leave the same-named method on the unrelated class censused"
    )
    assert scan_unreferenced_symbols(
        tree,
        candidates,
        framework_callbacks={("fixture_module.py", "Panel", "sizeHint"): object},
    ) == unexempted, "a base class that does not declare the name exempts nothing"

    class DeclaresSizeHint:
        def sizeHint(self, option, index):
            return None

    assert scan_unreferenced_symbols(
        tree,
        candidates,
        framework_callbacks={
            ("fixture_module.py", "Panel", "sizeHint"): DeclaresSizeHint
        },
    ) == unexempted, "a base the declaring class does not inherit exempts nothing"

    document = "docs/tasks/task-graph.json — AC3 registers Panel.sizeHint"
    assert citation_violation(
        "fixture_module.py", "Panel.sizeHint", document, tree
    ), "a document mention satisfied the method citation check"
    assert scan_unreferenced_symbols(
        tree,
        candidates,
        allowlist={"fixture_module.py": {"Panel.sizeHint": document}},
    ) == unexempted, "a document mention in the allowlist must exempt nothing"
    assert scan_unreferenced_symbols(
        tree,
        candidates,
        framework_callbacks={
            ("fixture_module.py", "Panel", "sizeHint"): document
        },
    ) == unexempted, "a string is not a base class, so it cannot exempt a method"


def test_framework_exemption_is_consulted_independently_of_reachability():
    """AC3: a bare/string mention rescues nothing; the entry still exempts."""
    tree = _framework_fixture_tree()
    tree["loose_mentions.py"] = (
        "LABEL = \"sizeHint\"\n"
        "\n"
        "\n"
        "def note(sizeHint):\n"
        "    return sizeHint\n"
    )
    candidates = {"fixture_module.py": _class_methods(tree["fixture_module.py"])}
    entry = {("fixture_module.py", "Panel", "sizeHint"): QStyledItemDelegate}
    assert scan_unreferenced_symbols(tree, candidates) == [
        "fixture_module.py:Panel.sizeHint",
        "fixture_module.py:Plain.sizeHint",
    ], "a string constant and a bare argument name are not method evidence"
    assert scan_unreferenced_symbols(
        tree, candidates, framework_callbacks=entry
    ) == ["fixture_module.py:Plain.sizeHint"], (
        "the exemption is consulted independently of reachability: it exempts "
        "the class that inherits the base and still censuses the unrelated one"
    )
    real_tree = sources()
    assert _framework_callback_exempt(
        "ui/option_spreads_panel.py",
        "_ElideNameDelegate",
        "initStyleOption",
        FRAMEWORK_CALLBACKS,
        real_tree,
    ), "_ElideNameDelegate.initStyleOption must stay exempt through its entry"
    assert _framework_callback_exempt(
        "ui/option_spreads_panel.py",
        "OptionSpreadsPanel",
        "sizeHint",
        FRAMEWORK_CALLBACKS,
        real_tree,
    ), "OptionSpreadsPanel.sizeHint must stay exempt through its entry"
    assert scan_unreferenced_symbols(
        real_tree,
        _census_candidates(real_tree),
        CENSUS_ALLOWLIST,
        FRAMEWORK_CALLBACKS,
    ) == [], "the real tree must be green with the framework table supplied"


def test_p23_framework_callbacks_stay_green_through_their_cited_form():
    """AC3: the tree's own initStyleOption/sizeHint resolve against their base."""
    tree = sources()
    candidates = _census_candidates(tree)
    assert set(FRAMEWORK_CALLBACKS) == {
        ("ui/option_spreads_panel.py", "_ElideNameDelegate", "initStyleOption"),
        ("ui/option_spreads_panel.py", "OptionSpreadsPanel", "sizeHint"),
    }
    assert FRAMEWORK_CALLBACKS[
        ("ui/option_spreads_panel.py", "_ElideNameDelegate", "initStyleOption")
    ] is QStyledItemDelegate
    assert FRAMEWORK_CALLBACKS[
        ("ui/option_spreads_panel.py", "OptionSpreadsPanel", "sizeHint")
    ] is QWidget
    for (module, declaring_class, method), base in FRAMEWORK_CALLBACKS.items():
        assert _framework_callback_exempt(
            module, declaring_class, method, FRAMEWORK_CALLBACKS, tree
        ), f"{module}:{declaring_class}.{method} does not resolve against its base"
        assert f"{declaring_class}.{method}" in candidates[module]
    assert scan_unreferenced_symbols(
        tree, candidates, CENSUS_ALLOWLIST, FRAMEWORK_CALLBACKS
    ) == []


# ---------------------------------------------------------------------------
# The gate must be RED on a seeded fixture before it is trusted green
# ---------------------------------------------------------------------------


def test_clause_i_reachability_is_production_only():
    """AC1: a reference that lives only under tests/ is never a caller."""
    production = {
        "prod_module.py": (
            "def leftover_helper(value):\n"
            "    return value\n"
            "\n"
            "\n"
            "def own_module_helper(value):\n"
            "    return value\n"
            "\n"
            "\n"
            "def own_caller():\n"
            "    return own_module_helper(2)\n"
        ),
        "tests/test_user.py": (
            "from prod_module import leftover_helper\n"
            "\n"
            "\n"
            "def test_it():\n"
            "    assert leftover_helper(1) == 1\n"
        ),
    }
    candidates = {"prod_module.py": ("leftover_helper", "own_module_helper")}
    assert scan_unreferenced_symbols(production, candidates) == [
        "prod_module.py:leftover_helper"
    ], "a reference that exists only under tests/ must not satisfy a caller"
    assert scan_unreferenced_symbols(
        production, {"prod_module.py": ("own_module_helper",)}
    ) == [], "a helper used inside its own production module is green"
    with_production_caller = dict(production)
    with_production_caller["prod_caller.py"] = (
        "from prod_module import leftover_helper\n"
        "\n"
        "\n"
        "def poke():\n"
        "    return leftover_helper(3)\n"
    )
    assert scan_unreferenced_symbols(with_production_caller, candidates) == [], (
        "a production caller must clear the symbol"
    )
    # The pool is the parameter: naming the tests file explicitly is the only
    # way a tests/ reference can count, and the default never includes it.
    assert scan_unreferenced_symbols(
        production,
        {"prod_module.py": ("leftover_helper",)},
        reachability_tree={
            **production,
            "tests/test_user.py": production["tests/test_user.py"],
        },
    ) == [], "reachability_tree is the pool, and it is honoured verbatim"
    tree = sources()
    assert any(path.startswith(TEST_DIR + "/") for path in tree), (
        "the full tree must still carry tests/ for clauses (ii) and (iii)"
    )
    assert all(suite in tree for suite in P23_SUITES), (
        "clause (ii)'s suites are tests/ files and must stay in the scanned tree"
    )
    assert _unreferenced_helpers("def _orphan_helper():\n    return 1\n") == [
        "_orphan_helper"
    ], "clause (ii) must still find a helper in a test-file source"
    assert _token_offences(_text("tests/test_d65_residue.py")), (
        "clause (iii)'s token sweep must still read tests/"
    )


def test_clause_i_method_evidence_is_class_bound():
    """AC2: only the declaring class's own bound member is evidence."""
    fixture = {
        "fixture_module.py": (
            "class Owner:\n"
            "    def close(self):\n"
            "        return None\n"
            "\n"
            "\n"
            "class Other:\n"
            "    def close(self):\n"
            "        return None\n"
        ),
        "user_module.py": (
            "from fixture_module import Other\n"
            "\n"
            "\n"
            "def close():\n"
            "    return None\n"
            "\n"
            "\n"
            "def poke(close):\n"
            "    Other().close()\n"
            "    return close\n"
        ),
    }
    candidates = {"fixture_module.py": _class_methods(fixture["fixture_module.py"])}
    assert scan_unreferenced_symbols(fixture, candidates) == [
        "fixture_module.py:Owner.close"
    ], (
        "a same-named attribute on an unrelated class, a bare name, an argument "
        "name and a module-level symbol of the same spelling are not evidence "
        "for Owner.close"
    )
    bound = dict(fixture)
    bound["user_module.py"] += (
        "\n\n"
        "def wire():\n"
        "    owner = Owner()\n"
        "    owner.close()\n"
    )
    assert scan_unreferenced_symbols(bound, candidates) == [], (
        "owner = Owner(); owner.close() must resolve to Owner's member"
    )
    annotated = dict(fixture)
    annotated["user_module.py"] = (
        "from fixture_module import Owner\n"
        "\n"
        "\n"
        "def drive(owner: Owner):\n"
        "    owner.close()\n"
    )
    assert scan_unreferenced_symbols(
        annotated, {"fixture_module.py": ("Owner.close", "Other.close")}
    ) == ["fixture_module.py:Other.close"], (
        "an annotated parameter is class-bound evidence; the other class is not"
    )
    string_only = dict(fixture)
    string_only["user_module.py"] = (
        "from fixture_module import Other\n"
        "\n"
        "\n"
        "def poke():\n"
        "    return getattr(Other(), \"close\")\n"
    )
    assert scan_unreferenced_symbols(
        string_only, {"fixture_module.py": ("Owner.close", "Other.close")}
    ) == ["fixture_module.py:Other.close", "fixture_module.py:Owner.close"], (
        "a string constant is not method evidence under the class-bound rule"
    )
    tree = dict(sources())
    engine_module = "services/option_spread_engine.py"
    tree[engine_module] += "\n    def close(self):\n        return None\n"
    assert "conn.close()" in tree["data/db_backup.py"], (
        "the fixture's premise: `close` occurs elsewhere in the tree"
    )
    assert scan_unreferenced_symbols(
        tree, {engine_module: ("SpreadEngine.close",)}
    ) == [f"{engine_module}:SpreadEngine.close"], (
        "a common method name elsewhere cannot hide an orphaned method"
    )


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
        sources(),
        _census_candidates(sources()),
        CENSUS_ALLOWLIST,
        FRAMEWORK_CALLBACKS,
    ), "the real tree must be green"


@pytest.fixture()
def dead_method_fixture(tmp_path):
    """A two-module tree: a class method its caller calls, one nothing calls."""
    fixture_source = (
        "class Owner:\n"
        "    def used_method(self):\n"
        "        return 1\n"
        "\n"
        "    def orphan_method(self):\n"
        "        return 2\n"
    )
    caller_source = (
        "from fixture_module import Owner\n"
        "\n"
        "\n"
        "def drive(owner: Owner):\n"
        "    return owner.used_method()\n"
    )
    (tmp_path / "fixture_module.py").write_text(fixture_source, encoding="utf-8")
    (tmp_path / "caller_module.py").write_text(caller_source, encoding="utf-8")
    return {
        "fixture_module.py": fixture_source,
        "caller_module.py": caller_source,
    }


def test_gate_is_red_on_a_seeded_dead_method_and_follows_the_call_site(
    dead_method_fixture,
):
    """AC2: the method census answers call sites, not class membership."""
    candidates = {
        "fixture_module.py": _class_methods(
            dead_method_fixture["fixture_module.py"]
        )
    }
    assert scan_unreferenced_symbols(dead_method_fixture, candidates) == [
        "fixture_module.py:Owner.orphan_method"
    ], "exactly the method nothing calls must be reported"
    mutated = dict(dead_method_fixture)
    mutated["caller_module.py"] = (
        "from fixture_module import Owner\n"
        "\n"
        "\n"
        "def drive(owner: Owner):\n"
        "    return owner\n"
    )
    assert scan_unreferenced_symbols(mutated, candidates) == [
        "fixture_module.py:Owner.orphan_method",
        "fixture_module.py:Owner.used_method",
    ], "removing the only call site must add exactly the called method"
    assert not scan_unreferenced_symbols(
        sources(), _census_candidates(sources()), CENSUS_ALLOWLIST,
        FRAMEWORK_CALLBACKS,
    ), "the real tree must stay green in the same run"


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
    assert "live-TWS" in GATE_RECORD, (
        "the record must describe AC-D65.19 as the live-TWS acceptance run"
    )
    assert "owned by P23-T26" in GATE_RECORD, (
        "the record must name P23-T26 as AC-D65.19's owner"
    )
    assert "NOT claimed" in GATE_RECORD
    # Built from two pieces so this assertion does not spell the retired phrase
    # in the very file it checks: a plain literal would trip its own grep.
    retired = "paper" + "-TWS acceptance run"
    assert retired not in GATE_RECORD
    for rel in (
        "tests/test_d65_residue.py",
        "tests/test_d65_acceptance_record.py",
    ):
        assert retired not in _text(rel), rel


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
    # `7435/7455` is AC-D65.9(i)'s **legal** 20-wide pair, exercised by the
    # ladder suite's own pair cases; only A212's two typos are banned. Guard the
    # ban list itself so a later tidy cannot widen it to a legal pair.
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
