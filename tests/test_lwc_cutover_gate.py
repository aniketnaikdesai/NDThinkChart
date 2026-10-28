"""P6-T12 — Phase 10 packaging + CI + cutover candidate gate (AC-D47.6,
AC-D47.8, AC-D47.9; S59 triple gate, no soak).

The cutover gate is three independent proofs plus a boundary proof, because
"the candidate is declared, not shipped" can fail four ways:

1. **the bundle would not carry the engine** — both PyInstaller specs must name
   the vendored ``chart_assets/lwc`` tree as ``datas`` and the QtWebEngine
   modules as ``hiddenimports`` (AC-D47.6). Parsed with ``ast`` from the spec
   source, so a spec that merely mentions the words in a comment fails;
2. **the size/signing disposition would be invented** — the record must recite
   the *measured* P6-01 delta (``docs/lwc_spike_results.md``, Q61/A109) and the
   tree it now absorbs, with no fixed budget and no fabricated Chromium figure
   (measure-first);
3. **CI would not run the suite** — ``.github/workflows/lwc_parity.yml`` must
   run the offscreen Python suite, keep ``@pytest.mark.webengine`` cases as
   skips (never red, DG88/AP-P6-4), run ``node --test chart_assets/lwc/`` and
   hold the 19-row parity matrix; the file is structurally validated here
   (no PyYAML in this venv);
4. **the default would have been flipped** — the parity matrix must be
   19 rows, every non-accepted non-retired row must carry an explicit
   rule-10 entry, rows 16/17 must be Done/accepted and row 19 must be
   Retired (P6-T13 as-built + coverage ledger), the Phase-0 perf floor
   and still met. P6-12 pinned pyqtgraph as present and the default; P6-13
   default engine with nothing deleted (AC-D47.9; P6-13 is separately gated).

The residue scan at the bottom is the renderer-only boundary (``ibkr/``, DB
schema/store API, service signatures, watchlist/dock/persistence, order code)
plus the deletion-set probe: every retained engine module must still exist.

P6-12 flipped no default and deleted nothing. P6-13 (owner-waived gate)
removed the engine afterwards; the engine-present assertions below were
retired with it, and the packaging assertion now requires its absence.
"""

from __future__ import annotations

import ast
import json
import os
import re
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent

_ROOT_SPEC = "NDThinkChart.spec"
_PACKAGED_SPEC = "packaging/build.spec"
_SPECS = (_ROOT_SPEC, _PACKAGED_SPEC)

_WORKFLOW = ".github/workflows/lwc_parity.yml"
_MATRIX = "docs/lwc_parity_matrix.md"
_SPIKE_RESULTS = "docs/lwc_spike_results.md"

#: Destination the LWC tree must land at inside the bundle — the same relative
#: path ``ui/lwc_host.ASSET_DIR`` serves through ``ndt://lwc/``.
_LWC_DEST = "chart_assets/lwc"

#: Modules whose presence proves the WebEngine host/bridge was not pruned.
_WEBENGINE_MODULES = (
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebChannel",
)

#: The assets the offline page (``chart.html``) resolves at runtime. The whole
#: directory ships, so this is the canary set, not the full list.
_REQUIRED_ASSETS = (
    "chart.html",
    "chart.js",
    "envelope.js",
    "lightweight-charts.standalone.production.js",
    "VERSION",
    "ATTRIBUTION.md",
)

#: Phase-0 measured baseline, pinned here so a silent relaxation of the record
#: fails the gate (values live in ``docs/lwc_spike_results.md``).
_BASELINE_BUNDLE_KB = "378,400"
_BASELINE_BUILD_MS = "1.3 ms"
_BASELINE_PAYLOAD_BYTES = "533,265"
_BASELINE_SERIALIZE_MS = "5.5 ms"

#: Measured this wave (P6-T12): the vendored tree the bundle now absorbs.
_MEASURED_TREE_BYTES = "338,928"
_MEASURED_DELTA_PCT = "0.09"

#: Floors the live perf probe must beat. Generous absolute ceilings (10x the
#: Phase-0 figures) so a slow CI runner cannot flake, while an order-of-
#: magnitude regression still fails.
_BUILD_CEILING_MS = 13.0
_SERIALIZE_CEILING_MS = 55.0

#: Retained engine surface after P6-13: the seam, the LWC driver/host/bridge
#: and the shared model. The pyqtgraph render modules are gone.
_RETAINED_ENGINE_FILES = (
    "ui/chart_controls.py",
    "ui/chart_mouse_router.py",
    "ui/popout_window.py",
    "ui/chart_view.py",
    "ui/lwc_view.py",
    "ui/lwc_host.py",
    "ui/lwc_bridge.py",
    "services/chart_model.py",
)

#: Surfaces the renderer-only boundary forbids in this task's own footprint
#: (packaging + CI are build plumbing, never backend or store plumbing).
_FORBIDDEN_IN_PACKAGING = (
    "ibkr",
    "DrawingStore",
    "AlarmStore",
    "PopoutStore",
    "watchlist",
    "order_service",
    "trade_group",
)


def _read(rel: str) -> str:
    return (_REPO / rel).read_text(encoding="utf-8")


def _analysis_kwargs(rel: str) -> dict[str, ast.AST]:
    """Return the ``Analysis(...)`` keyword nodes of a spec file, by name."""
    tree = ast.parse(_read(rel), filename=rel)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Analysis":
            return {kw.arg: kw.value for kw in node.keywords if kw.arg}
    raise AssertionError(f"{rel}: no Analysis(...) call found")


def _list_dests(node: ast.AST) -> list[str]:
    """String destinations of a ``datas`` list (second element of each tuple)."""
    dests: list[str] = []
    if not isinstance(node, ast.List):
        return dests
    for element in node.elts:
        if isinstance(element, ast.Tuple) and len(element.elts) == 2:
            dest = element.elts[1]
            if isinstance(dest, ast.Constant) and isinstance(dest.value, str):
                dests.append(dest.value)
    return dests


def _list_constants(node: ast.AST) -> list[str]:
    if not isinstance(node, ast.List):
        return []
    return [
        elt.value
        for elt in node.elts
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
    ]


def _matrix_rows() -> dict[int, dict[str, str]]:
    """Parse the parity matrix table: row number -> cells."""
    rows: dict[int, dict[str, str]] = {}
    for line in _read(_MATRIX).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 6 or not cells[0].isdigit():
            continue
        rows[int(cells[0])] = {
            "row": cells[1],
            "gate_wave": cells[4],
            "disposition": cells[5],
        }
    return rows


def _p612_section() -> str:
    """The P6-12 wave-exit note (from its heading to the next ``### ``)."""
    text = _read(_MATRIX)
    match = re.search(r"\n### P6-12 .*?(?=\n### |\Z)", text, re.DOTALL)
    assert match, "docs/lwc_parity_matrix.md has no P6-12 wave-exit note"
    return match.group(0)


def _rule10_section() -> str:
    text = _read(_MATRIX)
    match = re.search(r"\n## Rule-10 entries.*?(?=\n## |\n### |\Z)", text, re.DOTALL)
    assert match, "docs/lwc_parity_matrix.md has no '## Rule-10 entries' section"
    return match.group(0)


# ── P6-T12-T11 — bundle wiring, measured disposition, CI ──────────────────


@pytest.mark.parametrize("spec", _SPECS)
def test_specs_ship_the_vendored_tree_and_webengine(spec: str) -> None:
    """AC1/AC-D47.6: both specs carry the LWC tree as data, WebEngine as imports."""
    kwargs = _analysis_kwargs(spec)

    assert "datas" in kwargs, f"{spec}: Analysis() has no datas list"
    dests = _list_dests(kwargs["datas"])
    assert _LWC_DEST in dests, (
        f"{spec}: the vendored tree is not bundled — expected a datas entry "
        f"with destination {_LWC_DEST!r}, found {dests}"
    )
    # The tree must land as a directory of assets, and the resolved source must
    # be the shipped tree (constant path in the root spec, ``_lwc_dir`` in the
    # packaged one), never an empty or renamed directory.
    assert (len(dests) >= 1) and "config" in dests, f"{spec}: theme datas lost"

    hidden = _list_constants(kwargs.get("hiddenimports", ast.List(elts=[])))
    for module in _WEBENGINE_MODULES:
        assert module in hidden, (
            f"{spec}: {module} missing from hiddenimports — PyInstaller would "
            f"prune the WebEngine host/bridge (and Chromium) from the app"
        )

    # P6-13 removed the pyqtgraph engine: the spec must not name it.
    assert "pyqtgraph" not in hidden, f"{spec}: pyqtgraph is still packaged"


def test_vendored_tree_is_complete_and_offline() -> None:
    """AC1: the bundled directory holds the offline page and its relative assets."""
    tree = _REPO / _LWC_DEST
    assert tree.is_dir(), f"{_LWC_DEST} is missing from the source tree"
    for name in _REQUIRED_ASSETS:
        assert (tree / name).is_file(), f"{_LWC_DEST}/{name} missing"

    html = (tree / "chart.html").read_text(encoding="utf-8")
    assert "http://" not in html and "https://" not in html, (
        "chart.html references a remote URL — the offline case would fail"
    )
    for asset in ("lightweight-charts.standalone.production.js", "envelope.js", "chart.js"):
        assert f'./{asset}"' in html or f'"{asset}"' in html or asset in html, (
            f"chart.html does not load {asset}"
        )


def test_size_delta_and_signing_disposition_are_measured() -> None:
    """AC1: the disposition recites the measured P6-01 delta; nothing invented."""
    spike = _read(_SPIKE_RESULTS)
    for pinned in (
        _BASELINE_BUNDLE_KB,
        _BASELINE_BUILD_MS,
        _BASELINE_PAYLOAD_BYTES,
        _BASELINE_SERIALIZE_MS,
        "Signing-flow finding",
    ):
        assert pinned in spike, (
            f"docs/lwc_spike_results.md no longer holds the Phase-0 baseline "
            f"token {pinned!r} — the gate's floor was silently changed"
        )
    assert re.search(r"no fixed (size )?budget", spike, re.I), (
        "docs/lwc_spike_results.md no longer states the measure-first policy"
    )
    assert "measure-first" in spike.lower()

    note = _p612_section()
    assert _BASELINE_BUNDLE_KB in note, (
        "the P6-12 note does not recite the measured P6-01 .app baseline"
    )
    assert _MEASURED_TREE_BYTES in note, (
        "the P6-12 note does not record the measured vendored-tree bytes the "
        "bundle now absorbs"
    )
    assert _MEASURED_DELTA_PCT in note, "the P6-12 note does not record the delta percent"
    assert re.search(r"no fixed (size )?budget", note, re.I), (
        "the disposition must state that no budget is invented (Q61/A109)"
    )
    assert "not measured" in note.lower() or "unmeasured" in note.lower(), (
        "the Chromium term must be recorded as unmeasured, not invented"
    )
    assert "codesign_identity=None" in note, (
        "the signing disposition must name today's actual flow"
    )
    assert "nested" in note.lower(), (
        "the signing finding must name the nested-binary obligation QtWebEngine adds"
    )
    assert "P6-13" in note and "S59" in note, (
        "the declaration must name the separately gated removal + live-session gate"
    )


def test_ci_workflow_exists_is_valid_and_runs_the_suite() -> None:
    """AC1/AC-D47.9: CI runs offscreen + webengine-skips + node --test + rows."""
    path = _REPO / _WORKFLOW
    assert path.is_file(), f"{_WORKFLOW} is missing"
    text = path.read_text(encoding="utf-8")

    problem = _structural_yaml_problem(text)
    assert problem is None, f"{_WORKFLOW}: {problem}"

    required = (
        "name: LWC parity",
        "jobs:",
        "runs-on:",
        "QT_QPA_PLATFORM: offscreen",
        "tests/test_lwc_cutover_gate.py",
        '-m "not webengine"',
        "-m webengine",
        "node --test chart_assets/lwc/",
        "lwc_parity_matrix.md",
        "actions/checkout@",
    )
    for token in required:
        assert token in text, f"{_WORKFLOW} is missing {token!r}"

    # webengine cases must be proven as skips, never red.
    assert re.search(r"webengine cases skip cleanly", text, re.I), (
        "CI has no explicit webengine skip-never-red step"
    )
    assert "never red" in text.lower()
    # The row-count gate must assert 19, not merely print it.
    assert re.search(r"row count", text, re.I) and "19" in text

    # Offscreen is exported for every step, not inline in one command only.
    env_block = re.search(r"env:\n((?:\s+.*\n)+)", text)
    assert env_block and "QT_QPA_PLATFORM" in env_block.group(1), (
        "QT_QPA_PLATFORM must be job-level so every step runs offscreen"
    )


def _structural_yaml_problem(text: str) -> str | None:
    """Conservative YAML validity check (no PyYAML in this venv).

    Accepts the subset this workflow uses: mapping entries ``key:``, ``- item``
    list entries that are mappings, comments, and block scalars (``|``/``>``
    whose indented body is skipped). Rejects tabs (illegal for YAML
    indentation), a scalar where a mapping is required, and a list item with no
    key. Returns ``None`` when the document is well formed.
    """
    block_indent: int | None = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            return f"line {lineno}: tab character (illegal YAML indentation)"
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip(" "))
        if block_indent is not None:
            if not stripped or indent > block_indent:
                continue
            block_indent = None
        if not stripped or stripped.startswith("#") or stripped in ("---", "..."):
            continue
        if re.search(r":\s*[|>][-+0-9]*\s*$", raw):
            block_indent = indent
            continue
        if stripped.startswith("- "):
            body = stripped[2:].strip()
            if body and ":" not in body:
                return f"line {lineno}: list item is a bare scalar, expected a mapping"
            continue
        if not re.match(r"[^\s:#][^:]*:(\s|$)", stripped):
            return f"line {lineno}: not a mapping entry: {stripped!r}"
    return None


# ── P6-T12-T12 — the triple gate (parity + perf) ──────────────────────────


def test_matrix_is_19_rows_and_every_open_row_has_a_rule10_entry() -> None:
    """AC2: parity all Done/accepted, row 19 Retired recorded, or an explicit rule-10 entry — never a hole."""
    rows = _matrix_rows()
    assert len(rows) == 19, f"parity matrix must hold 19 rows, found {len(rows)}"
    assert set(rows) == set(range(1, 20)), "parity matrix row numbers are not 1..19"

    done = {n for n, row in rows.items() if "done / accepted" in row["disposition"].lower()}
    retired = {n for n, row in rows.items() if "retired" in row["disposition"].lower()}
    # P6-T13 retired the oracle with owner approval: row 19 is Retired, and
    # it is the only row allowed outside Done/Open — fail closed.
    assert retired == {19}, sorted(retired)
    cell_19 = rows[19]["disposition"]
    assert "Retired" in cell_19, cell_19
    lowered_19 = cell_19.lower()
    assert "as-built" in lowered_19 and "p6-t13" in lowered_19, cell_19
    assert "retired coverage" in _read(_MATRIX).lower(), (
        "parity matrix has no Retired coverage ledger for row 19"
    )
    pending = sorted(set(rows) - done - retired)
    for required in (16, 17):
        assert required in done, (
            f"row {required} ({rows[required]['row']}) must be Done/accepted for "
            f"the cutover candidate — it is {rows[required]['disposition']!r}"
        )

    rule10 = _rule10_section()
    for number in pending:
        assert re.search(rf"\bRow {number}\b[^\n]*Rule-10 entry", rule10, re.I), (
            f"row {number} is Open/pending without a rule-10 entry"
        )
    assert "regressing" in rule10.lower(), "the rule-10 section must restate rule 10"

    # The summary counts must agree with the table — a stale line fails here.
    text = _read(_MATRIX)
    summary = re.search(
        r"Row count:\s*(\d+)\.\s*Dispositioned Open/pending:\s*(\d+)\.\s*Done/accepted:\s*(\d+)\.",
        text,
    )
    assert summary, "the matrix has no row-count summary line"
    assert int(summary.group(1)) == 19
    assert int(summary.group(2)) == len(pending), (
        f"summary says {summary.group(2)} Open/pending, table has {len(pending)}"
    )
    assert int(summary.group(3)) == len(done), (
        f"summary says {summary.group(3)} Done/accepted, table has {len(done)}"
    )


def test_candidate_is_declared_not_shipped() -> None:
    """AC2/AC-D47.9: declared, pyqtgraph still default, no deletion."""
    note = _p612_section()
    assert re.search(r"cutover candidate (is )?declared", note, re.I), (
        "the P6-12 note must declare the cutover candidate explicitly"
    )
    assert "not shipped" in note.lower() or "no-soak" in note.lower()
    assert "pyqtgraph" in note.lower() and "default" in note.lower()
    assert re.search(r"no\s+pyqtgraph\s+code\s+was\s+deleted", note, re.I), (
        "the declaration must state that no pyqtgraph code was deleted"
    )
    assert "owner" in note.lower() and "Q61" in note and "A109" in note, (
        "the owner-acceptance leg must be recorded (Q61/A109)"
    )
    assert "soak" in note.lower(), "the no-soak decision must be recorded (S59)"






def test_phase0_perf_baseline_holds() -> None:
    """AC2: the Phase-0 floor is unchanged and still met (no soak, no budget)."""
    spike = _read(_SPIKE_RESULTS)
    assert "Phase-0 perf baseline" in spike
    for pinned in (_BASELINE_BUILD_MS, _BASELINE_PAYLOAD_BYTES, _BASELINE_SERIALIZE_MS):
        assert pinned in spike

    rows = _build_bars(5000)

    build_ms = _best_ms(lambda: _build_bars(5000))
    assert build_ms <= _BUILD_CEILING_MS, (
        f"5,000-bar OHLC build regressed: {build_ms:.2f} ms "
        f"(Phase-0 1.3 ms, ceiling {_BUILD_CEILING_MS} ms)"
    )

    payload = json.dumps(_history_envelope(rows), separators=(",", ":")).encode()
    serialize_ms = _best_ms(
        lambda: json.dumps(_history_envelope(rows), separators=(",", ":")).encode()
    )
    assert serialize_ms <= _SERIALIZE_CEILING_MS, (
        f"history envelope serialization regressed: {serialize_ms:.2f} ms "
        f"(Phase-0 5.5 ms, ceiling {_SERIALIZE_CEILING_MS} ms)"
    )
    assert 200_000 <= len(payload) <= 1_500_000, (
        f"the 5,000-bar envelope is {len(payload)} bytes — the payload the "
        f"Phase-0 baseline was measured on must still be transported whole"
    )


def _build_bars(count: int) -> list[dict[str, float]]:
    start = 1_700_000_000
    bars = []
    for index in range(count):
        base = 100.0 + (index % 37) * 0.01
        bars.append(
            {
                "ts": start + index * 60,
                "open": base,
                "high": base + 0.5,
                "low": base - 0.4,
                "close": base + 0.2,
                "volume": 1000 + index,
            }
        )
    return bars


def _history_envelope(rows: list[dict[str, float]]) -> dict:
    return {
        "v": 1,
        "ops": [
            {
                "op": "set_data",
                "series": "candles",
                "cols": {
                    "ts": [row["ts"] for row in rows],
                    "o": [row["open"] for row in rows],
                    "h": [row["high"] for row in rows],
                    "l": [row["low"] for row in rows],
                    "c": [row["close"] for row in rows],
                    "v": [row["volume"] for row in rows],
                },
            }
        ],
    }


def _best_ms(callable_, repeats: int = 3) -> float:
    best = float("inf")
    for _ in range(repeats):
        start = time.perf_counter()
        callable_()
        best = min(best, (time.perf_counter() - start) * 1000.0)
    return best


# ── P6-T12-T13 — residue scan (no engine deletion, no backend change) ─────


def test_deletion_set_is_untouched() -> None:
    """AC3: every retained engine module still exists after the P6-13 removal."""
    missing = [rel for rel in _RETAINED_ENGINE_FILES if not (_REPO / rel).is_file()]
    assert not missing, f"pyqtgraph engine code was deleted before P6-13: {missing}"


def test_packaging_and_ci_touch_no_backend_surface() -> None:
    """AC3: build plumbing references no broker/DB/persistence/order surface."""
    for rel in (_ROOT_SPEC, _PACKAGED_SPEC, _WORKFLOW):
        text = _read(rel).lower()
        for forbidden in _FORBIDDEN_IN_PACKAGING:
            assert forbidden.lower() not in text, (
                f"{rel} references the out-of-scope backend surface {forbidden!r}"
            )


def test_boundary_records_are_kept() -> None:
    """AC3: the wave note states the renderer-only boundary and value channel."""
    note = _p612_section()
    lowered = note.lower()
    for surface in ("ibkr/", "db schema", "service signature", "watchlist", "order"):
        assert surface in lowered, (
            f"the P6-12 note must record the {surface!r} half of the boundary"
        )
    assert "timestamp" in lowered and "price" in lowered, (
        "the note must record that JS receives timestamps and prices only"
    )


@pytest.fixture(scope="module")
def qapp():
    """One offscreen ``QApplication`` for the construction-level probes."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
