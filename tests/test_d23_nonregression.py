"""D23-03 (Phase 3) — cross-cutting record-consistency and guard/invariant checks.

Batch 17 (D23) closes with an independent, re-runnable verification of the two
D22 post-build corrections:

  * **D23.1 / ESC-030** — ``MarketDataManager.cancel_contract_details`` is a
    capability-guarded, documented best-effort cancel (the pinned
    ``ibapi 9.81.1.post1`` exposes no ``EClient.cancelContractDetails``);
  * **D23.2 / ESC-031** — ``WatchlistPanel.remove_symbol`` drops the removed
    row's own ``_row_data`` key so the row-key invariant holds after any
    removal (first / middle / last / only).

It also re-verifies the reconciliation **record** itself:

  * task-level ``AC-D22.2.3`` in ``docs/tasks/task-graph.json`` (task ``D22-02``)
    now mandates the guarded cancel and no longer mandates a bare
    ``client.cancelContractDetails(req_id)`` wire call;
  * architecture ``S3`` (the D23 increment row + the D22 reconciliation note)
    records the same capability-guarded best-effort cancel;
  * D22's feature criteria (``AC-D22.1``–``AC-D22.9``) are not reopened.

No test connects to live TWS or transmits an order (Q9): the guard/invariant
checks inject fakes and never call ``IBApiClient.connect``; the record checks
only read repository files. All tests run offscreen (``tests/conftest.py``
sets ``QT_QPA_PLATFORM=offscreen``).
"""

import ast
import inspect
import json
import os
import textwrap
from pathlib import Path

from PyQt6.QtCore import QSettings

from ibkr.market_data import MarketDataManager
from ui.watchlist_panel import WatchlistPanel

ROOT = Path(__file__).resolve().parents[1]
TASK_GRAPH = ROOT / "docs" / "tasks" / "task-graph.json"
ARCHITECTURE = ROOT / "docs" / "architecture.md"
REQUIREMENTS = ROOT / "docs" / "requirements" / "requirements.md"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _task_graph() -> dict:
    return json.loads(_read_text(TASK_GRAPH))


def _task(graph: dict, task_id: str) -> dict:
    for task in graph["tasks"]:
        if task.get("id") == task_id:
            return task
    raise AssertionError(f"task {task_id!r} not found in {TASK_GRAPH}")


def _criterion(task: dict, prefix: str) -> str:
    for ac in task["acceptance_criteria"]:
        if ac.startswith(prefix):
            return ac
    raise AssertionError(f"criterion {prefix!r} not found on task {task['id']}")


# ═════════════════════════════════════════════════════════════════════════════
# D23-03-T01 / AC-D23.1.4 — record consistency (task graph + architecture)
# ═════════════════════════════════════════════════════════════════════════════

def test_D23_03_T01_task_graph_ac_d22_2_3_mandates_guarded_cancel():
    """D22-02's task-level AC-D22.2.3 is corrected to the guarded cancel.

    It must reference the capability guard and the pinned-`ibapi` absence, and
    must no longer mandate a bare ``client.cancelContractDetails(req_id)`` call.
    """
    task = _task(_task_graph(), "D22-02")
    ac = _criterion(task, "AC-D22.2.3")

    # The correction record marker.
    assert "[CORRECTED by D23.1 / AC-D23.1.4]" in ac

    # The mandate is the guarded best-effort cancel.
    assert "capability-guarded best-effort cancel" in ac
    guarded = (
        "getattr(self.client, 'cancelContractDetails', None)" in ac
        or 'getattr(self.client, "cancelContractDetails", None)' in ac
    )
    assert guarded, "AC-D22.2.3 must reference the getattr capability guard"
    assert "only when present" in ac

    # The pinned-`ibapi` absence is stated.
    assert "9.81.1.post1" in ac
    assert "EClient.cancelContractDetails" in ac

    # The former bare wire-cancel mandate is explicitly superseded, not restated.
    assert "supersedes the former" in ac
    assert "it calls client.cancelContractDetails(req_id)" not in ac

    # D22's feature criteria are not reopened.
    assert "not reopened" in ac

    # The task description records the same corrected cancel.
    desc = task["description"]
    assert "capability-guarded best-effort cancel" in desc
    assert "cancelContractDetails" in desc


def test_D23_03_T01_architecture_s3_records_guarded_cancel():
    """Architecture S3 (D23 increment) + the D22 reconciliation note agree."""
    text = _read_text(ARCHITECTURE)

    # The D23 increment exists.
    assert "D23 increment — Batch 17" in text

    # The reconciled D23 S3 row records the capability-guarded best-effort cancel.
    assert "S3 *(reconciled)*" in text
    assert "capability-guarded best-effort contract-details cancel" in text
    guard = (
        "getattr(self.client, 'cancelContractDetails', None)" in text
        or 'getattr(self.client, "cancelContractDetails", None)' in text
    )
    assert guard, "D23 S3 must record the getattr capability guard"
    assert "call it only if present" in text
    assert "reconciles D22 architecture row `S3`" in text
    assert "supersedes the task-level `AC-D22.2.3`" in text

    # The D22 S3 row carries the binding reconciliation note back to D23.
    assert "S3 reconciled by D23 (2026-10-07)" in text
    assert "binding `AC-D23.1.4`" in text
    assert "reconciliation" in text


def test_D23_03_T01_no_d22_feature_criterion_reopened():
    """D22's feature criteria (AC-D22.1–AC-D22.9) are present and unwritten."""
    text = _read_text(REQUIREMENTS)

    # Each D22 feature criterion heading is intact (frozen text).
    expected = [
        "**AC-D22.1 (add affordance + placement — B15a)**",
        "**AC-D22.2 (modal input — B15b)**",
        "**AC-D22.3 (normalisation + empty/duplicate guards)**",
        "**AC-D22.4 (live IBKR validation before add — B16)**",
        "**AC-D22.5 (require connection — B16b)**",
        "**AC-D22.6 (remove — B14)**",
        "**AC-D22.7 (persisted across restarts)**",
        "**AC-D22.8 (non-regression — D21.5 / D21.11 / D14 / D21.13)**",
        "**AC-D22.9 (regression suite)**",
    ]
    for heading in expected:
        assert heading in text, f"D22 feature criterion altered or missing: {heading}"

    # The D23 section records that D22 is not reopened.
    assert "its feature criteria (`AC-D22.1`–`AC-D22.9`) stand" in text

    # Only the task-level AC-D22.2.3 carried the D23.1 correction; the sibling
    # task-level criteria on D22-02 are not reopened.
    task = _task(_task_graph(), "D22-02")
    corrected = [
        ac for ac in task["acceptance_criteria"]
        if "[CORRECTED by D23.1 / AC-D23.1.4]" in ac
    ]
    assert len(corrected) == 1
    assert corrected[0].startswith("AC-D22.2.3")


# ═════════════════════════════════════════════════════════════════════════════
# D23-03-T03 / AC-D23-P3.2 — independently re-verifiable guard/invariant checks
# ═════════════════════════════════════════════════════════════════════════════

def test_D23_03_T03_guard_source_shape():
    """D23.1 code-shape: no bare wire-cancel access; the guard + docs are present.

    This is the pre-fix-red / green-after code-shape check (red before the
    guard: a bare ``ast.Attribute`` ``cancelContractDetails`` access and no
    ``getattr`` guard); it reads the live source, so it re-confirms the fix
    from an independent module.
    """
    src = textwrap.dedent(
        inspect.getsource(MarketDataManager.cancel_contract_details)
    )
    tree = ast.parse(src)

    bare_attr = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr == "cancelContractDetails"
    ]
    assert bare_attr == [], "bare cancelContractDetails attribute access must be gone"
    assert "self.client.cancelContractDetails(" not in src

    guard = (
        "getattr(self.client, 'cancelContractDetails', None)" in src
        or 'getattr(self.client, "cancelContractDetails", None)' in src
    )
    assert guard, "the capability guard must be present"

    # The pinned-version absence, TWS termination and safety net are documented.
    assert "9.81.1.post1" in src
    assert "contractDetailsEnd" in src
    assert "ContractLookupService" in src
    assert "cancel_all" in src


class _FakeMdManager:
    """Minimal MarketDataManager double: unique reqIds, records cancellations."""

    def __init__(self):
        self._next = 1
        self.cancelled = []

    def req_mkt_data(self, contract):
        req_id = self._next
        self._next += 1
        return req_id

    def cancel_mkt_data(self, req_id):
        self.cancelled.append(req_id)


def _isolated_settings(path) -> QSettings:
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


def test_D23_03_T03_remove_symbol_row_data_invariant(qapp, tmp_path):
    """D23.2 invariant: ``set(_row_data.keys()) == set(range(rowCount()))``.

    Independently re-runs the last/first/middle/only removal sequence and
    asserts the row-key invariant holds after every removal. Uses fakes only —
    no live TWS, no order (Q9).
    """
    panel = WatchlistPanel(settings=_isolated_settings(tmp_path / "d23_03.ini"))
    try:
        panel.set_market_data_manager(_FakeMdManager())
        for symbol in ("AAPL", "MSFT", "TSLA"):
            panel.add_symbol(symbol, object())

        assert panel.table.rowCount() == 3
        assert set(panel._row_data.keys()) == {0, 1, 2}

        # Last row: the removed row's own key (2) must be dropped, not left stale.
        assert panel.remove_symbol("TSLA") is True
        assert panel.table.rowCount() == 2
        assert set(panel._row_data.keys()) == set(range(panel.table.rowCount()))

        # Middle row.
        assert panel.remove_symbol("MSFT") is True
        assert set(panel._row_data.keys()) == {0}

        # Only row left.
        assert panel.remove_symbol("AAPL") is True
        assert panel.table.rowCount() == 0
        assert panel._row_data == {}
    finally:
        panel.close()
