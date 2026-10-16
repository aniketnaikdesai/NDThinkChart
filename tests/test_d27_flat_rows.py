"""ESC-053 — hide flat (qty == 0) positions from the portfolio panel render.

Owner decision (2026-10-16, verbatim): "Hide qty==0 positions". The flat rows
are real broker holdings at flat size, so they stay in the ``positions`` DB
table; only the panel render hides them. Scope is the panel render path only
(``ui/active_portfolio_panel.py``) — ``ui/main_window.py`` is not touched.

AC1: no flat position appears as a rendered row, for either feed
     (``set_positions`` bulk or ``add_position`` single).
AC2: non-flat positions (positive long / negative short) all still render.
AC3: the panel's position list and its rendered rows stay index-aligned, so
     ``_on_selection_changed``'s ``self._positions[row]`` lookup still resolves
     to the row the user selected.
"""

from __future__ import annotations

from data.models import Position
from ui.active_portfolio_panel import ActivePortfolioPanel


def _make_panel(qapp) -> ActivePortfolioPanel:
    panel = ActivePortfolioPanel()
    panel.show()
    qapp.processEvents()
    return panel


def _pos(symbol: str, qty: float, con_id: int) -> Position:
    return Position(
        symbol=symbol,
        qty=qty,
        avg_cost=1.0,
        contract_type="stock",
        con_id=con_id,
    )


def _rendered_symbols(panel: ActivePortfolioPanel) -> list[str]:
    table = panel.positions_table
    return [table.item(row, 0).text() for row in range(table.rowCount())]


def test_p2_t37_flat_row_hidden_on_bulk_set(qapp):
    """AC1 — a qty == 0 position fed via ``set_positions`` is not rendered."""
    panel = _make_panel(qapp)
    panel.set_positions([
        _pos("SPXW0", 0.0, 1),
        _pos("AAPL", 10.0, 2),
    ])
    qapp.processEvents()

    assert panel.positions_table.rowCount() == 1
    symbols = _rendered_symbols(panel)
    assert "AAPL" in symbols
    assert "SPXW0" not in symbols


def test_p2_t37_flat_row_hidden_on_single_add(qapp):
    """AC1 — a qty == 0 position fed via ``add_position`` is not rendered."""
    panel = _make_panel(qapp)
    panel.set_positions([_pos("AAPL", 10.0, 2)])
    qapp.processEvents()
    before = panel.positions_table.rowCount()

    panel.add_position(_pos("SPXW0", 0.0, 1))
    qapp.processEvents()
    assert panel.positions_table.rowCount() == before
    assert "SPXW0" not in _rendered_symbols(panel)

    panel.add_position(_pos("MSFT", 4.0, 3))
    qapp.processEvents()
    assert panel.positions_table.rowCount() == before + 1
    assert "MSFT" in _rendered_symbols(panel)


def test_p2_t37_non_flat_positions_still_render(qapp):
    """AC2 — only qty == 0 is hidden; long and short both render."""
    panel = _make_panel(qapp)
    panel.set_positions([
        _pos("AAPL", 10.0, 1),
        _pos("TSLA", -3.0, 2),
        _pos("SPXW0", 0.0, 3),
    ])
    qapp.processEvents()

    assert panel.positions_table.rowCount() == 2
    symbols = _rendered_symbols(panel)
    assert "AAPL" in symbols
    assert "TSLA" in symbols


def test_p2_t37_rows_stay_index_aligned_with_position_list(qapp):
    """AC3 — rendered rows stay index-aligned with ``panel._positions``."""
    panel = _make_panel(qapp)
    panel.set_positions([
        _pos("AAPL", 10.0, 1),
        _pos("TSLA", -3.0, 2),
        _pos("SPXW0", 0.0, 3),
    ])
    qapp.processEvents()

    table = panel.positions_table
    assert table.rowCount() == len(panel._positions)
    for row in range(table.rowCount()):
        assert panel._positions[row].symbol == table.item(row, 0).text()

    table.selectRow(0)
    qapp.processEvents()
    assert panel._selected_position is not None
    assert panel._selected_position.symbol == table.item(0, 0).text()
