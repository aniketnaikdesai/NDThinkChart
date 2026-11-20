"""P30-02 / D102 + D103 — a transient surface dismissed by its owner, and a
selection restored by identity.

Two independent rules live here, in two independent classes so either can be
rejected without the other:

* :class:`TestWatchlistPopupDismissal` — D102.  ``_search_popup`` is a
  top-level ``Qt.Popup`` parented to the watchlist panel, so hiding
  ``header_bar``/``table`` cannot hide it.  Every collapse path must dismiss
  it *and* clear its items, and a result delivered after the collapse must
  not re-open it (``AC-D102.1`` / ``AC-D102.2``).
  ``test_a0_*`` first proves the measurement can see the un-fixed survivor
  (AR-P30-11): with the pre-fix body the popup is still open and its list
  still populated.  A case that cannot fail is not evidence.
* :class:`TestDrawingSelectionRestore` — D103.  ``reload()`` clears and
  repopulates ``drawings_list``; the selection the Assign / Ungroup / Delete
  actions read is restored **by drawing id**, never by row index, so a reload
  that reorders or shrinks the list keeps exactly the surviving ids
  (``AC-D103.1`` / ``AC-D103.2``).

All cases run offscreen against the shared temp DB from ``conftest.py``.
"""

from __future__ import annotations

import os

import pytest
from PyQt6.QtCore import QSettings, Qt

from data.drawing_store import DrawingStore
from data.models import Drawing
from ui.drawing_groups_dialog import DrawingGroupsDialog
from ui.watchlist_panel import WatchlistPanel

SYMBOL = "P30T2"


# ── D102 helpers ─────────────────────────────────────────────────────────────

def _desc(symbol, sec_type="STK", exchange="SMART"):
    from ibapi.contract import ContractDescription

    d = ContractDescription()
    d.contract.symbol = symbol
    d.contract.secType = sec_type
    d.contract.exchange = exchange
    return d


def _isolated_settings(path) -> QSettings:
    try:
        os.remove(path)
    except OSError:
        pass
    settings = QSettings(str(path), QSettings.Format.IniFormat)
    settings.clear()
    settings.sync()
    return settings


@pytest.fixture
def panel(qapp, tmp_path):
    """An offscreen panel backed by per-test settings (never the user's DB)."""
    p = WatchlistPanel(settings=_isolated_settings(tmp_path / "p30t2.ini"))
    yield p
    p.close()


def _popup_open(panel) -> bool:
    """True iff the popup is in the shown state.

    ``isHidden()`` is the platform-independent half (False = shown);
    ``isVisible()`` is included because the offscreen platform does report it
    for a ``Qt.Popup``, but it carries no extra information when a platform
    does not.
    """
    popup = panel._search_popup
    return (not popup.isHidden()) or popup.isVisible()


def _assert_dismissed(panel) -> None:
    popup = panel._search_popup
    assert popup.isHidden() is True
    assert popup.isVisible() is False
    assert _popup_open(panel) is False
    assert panel._search_list.count() == 0


def _pre_fix_collapse_visual(panel) -> None:
    """The pre-D102 body of ``_apply_collapsed_visual`` (four setVisible calls).

    Used only by the survivor proof below: it reproduces exactly what the
    un-fixed handler did, so the rest of the suite's assertion is checked
    against a case that can fail.
    """
    panel.header_bar.setVisible(False)
    panel.table.setVisible(False)
    panel.collapsed_bar.setVisible(True)
    panel.collapsed_handle.setVisible(True)


# ── D102 — case (a0): the measurement sees the un-fixed survivor (AR-P30-11) ─

def test_a0_measurement_detects_the_unfixed_survivor(panel):
    """AR-P30-11: the pre-fix handler leaves the popup visible with its items.

    Recorded survivor: on the pre-fix body ``_search_popup`` stayed shown
    (``isHidden() is False``, ``isVisible() is True``) with both result items
    still in ``_search_list`` — so the dismissal assertions in the cases that
    follow are not vacuous.
    """
    panel.show()
    panel.show_search_results([_desc("AAPL"), _desc("MSFT")])
    assert _popup_open(panel) is True
    assert panel._search_list.count() == 2

    _pre_fix_collapse_visual(panel)

    # The survivor: header/table hidden, popup still floating with stale items.
    assert panel._search_popup.isHidden() is False
    assert panel._search_popup.isVisible() is True
    assert _popup_open(panel) is True
    assert panel._search_list.count() == 2


# ── D102 — case (a): every collapse entry point dismisses the popup ──────────

COLLAPSE_ENTRY_POINTS = ("set_collapsed", "header_toggled", "toggle_collapsed")


@pytest.mark.parametrize("entry_point", COLLAPSE_ENTRY_POINTS)
def test_a_collapse_dismisses_popup_and_clears_items(panel, entry_point):
    """AC-D102.1: hidden and emptied, whichever path collapses the panel."""
    panel.show()
    panel.show_search_results([_desc("AAPL"), _desc("MSFT")])
    assert _popup_open(panel) is True
    assert panel._search_list.count() == 2

    if entry_point == "set_collapsed":
        panel.set_collapsed(True)
    elif entry_point == "header_toggled":
        panel._on_header_toggled(False)
    else:
        panel.toggle_collapsed()

    assert panel.is_collapsed() is True
    assert panel._search_popup.isHidden() is True
    assert panel._search_popup.isVisible() is False
    assert panel._search_list.count() == 0


# ── D102 — case (b): expansion does not resurrect a dismissed result ────────

def test_b_expansion_does_not_resurrect(panel):
    panel.show()
    panel.show_search_results([_desc("AAPL")])
    panel.set_collapsed(True)
    _assert_dismissed(panel)

    panel.set_collapsed(False)

    assert panel.is_collapsed() is False
    _assert_dismissed(panel)


# ── D102 — case (c): an in-flight delivery is refused, the guard is not mute ─

def test_c_in_flight_result_after_collapse_is_refused(panel):
    """AC-D102.2: the post-collapse delivery leaves the popup hidden/empty."""
    panel.show()
    panel.show_search_results([_desc("AAPL")])
    panel.set_collapsed(True)
    _assert_dismissed(panel)

    # The debounced lookup delivered its answer into the collapsed panel.
    panel.show_search_results([_desc("AAPL"), _desc("MSFT")])

    _assert_dismissed(panel)


def test_c_a_new_query_while_expanded_still_shows(panel):
    """The collapsed guard is a display decision, not a permanent mute."""
    panel.show()
    panel.show_search_results([_desc("AAPL")])
    panel.set_collapsed(True)
    panel.show_search_results([_desc("AAPL")])
    _assert_dismissed(panel)

    panel.set_collapsed(False)
    panel.show_search_results([_desc("NVDA")])

    assert _popup_open(panel) is True
    assert panel._search_list.count() == 1


# ── D102 — case (d): disabling search still clears (unchanged behaviour) ────

def test_d_disabling_search_still_clears(panel):
    panel.show()
    panel.set_search_enabled(True)
    panel.show_search_results([_desc("AAPL")])
    assert _popup_open(panel) is True

    panel.set_search_enabled(False)

    _assert_dismissed(panel)


# ── D103 helpers ────────────────────────────────────────────────────────────

def _make_drawing(label: str, group_id: int | None = None) -> Drawing:
    return Drawing(
        symbol=SYMBOL,
        kind="horizontal",
        payload={"y": 100.0},
        color="#38bdf8",
        label=label,
        group_id=group_id,
    )


@pytest.fixture
def seeded(qapp):
    """One group, three drawings; the dialog built over the shared temp DB."""
    gid = DrawingStore.create_group(SYMBOL, "Alpha", 1, "#38bdf8")
    ids = [
        DrawingStore.create_drawing(_make_drawing(f"drawing-{i}", gid))
        for i in range(3)
    ]
    dlg = DrawingGroupsDialog(SYMBOL)
    assert dlg.drawings_list.count() == 3
    yield dlg, gid, ids
    dlg.close()


def _select_drawings(dlg, ids) -> None:
    wanted = set(ids)
    for row in range(dlg.drawings_list.count()):
        item = dlg.drawings_list.item(row)
        item.setSelected(bool(item.data(Qt.ItemDataRole.UserRole) in wanted))


def _toggle_column(dlg, column: int) -> None:
    """Flip a group checkbox and drive the real handler once.

    ``setCheckState`` is applied with the table's signals blocked so the
    handler runs exactly once, from this call — the toggle path a user takes.
    """
    item = dlg.groups_table.item(0, column)
    dlg.groups_table.blockSignals(True)
    item.setCheckState(
        Qt.CheckState.Unchecked
        if item.checkState() == Qt.CheckState.Checked
        else Qt.CheckState.Checked
    )
    dlg.groups_table.blockSignals(False)
    dlg._on_group_item_changed(item)


# ── D103 — case (e): the visible toggle preserves the selection set ─────────

def test_e_visible_toggle_preserves_selection_and_assign_receives_it(
        seeded, monkeypatch):
    """AC-D103.1: ids before == ids after, and Assign is handed those ids."""
    dlg, gid, ids = seeded
    _select_drawings(dlg, ids[:2])
    before = dlg._selected_drawing_ids()
    assert before == ids[:2]

    recorded: list[tuple[list[int], object]] = []

    def _record(drawing_ids, group_id=None):
        recorded.append((list(drawing_ids), group_id))

    monkeypatch.setattr(DrawingStore, "assign_groups", staticmethod(_record))

    _toggle_column(dlg, 2)  # Visible

    after = dlg._selected_drawing_ids()
    assert after == before, (
        "the visible toggle wiped the drawing selection it had no business "
        "touching"
    )

    dlg.group_combo.setCurrentIndex(1)  # the one group
    dlg._assign_selected()

    assert recorded == [(ids[:2], gid)]


# ── D103 — case (f): the locked toggle behaves exactly like visible ─────────

def test_f_locked_toggle_preserves_selection(seeded):
    dlg, gid, ids = seeded
    _select_drawings(dlg, ids[:2])
    before = dlg._selected_drawing_ids()

    _toggle_column(dlg, 3)  # Locked

    assert dlg._selected_drawing_ids() == before
    assert DrawingStore.groups_for_symbol(SYMBOL)[0].locked is True


# ── D103 — case (g): a vanished id is skipped, not replaced by position ────

def test_g_vanished_selected_id_is_skipped(seeded):
    """AC-D103.2: the restored set is exactly the surviving id."""
    dlg, gid, ids = seeded
    _select_drawings(dlg, ids[:2])
    assert dlg._selected_drawing_ids() == ids[:2]

    DrawingStore.delete_drawing(ids[1])
    dlg.reload()

    assert dlg.drawings_list.count() == 2
    assert dlg._selected_drawing_ids() == [ids[0]]


# ── D103 — case (h): reordered rows restore the same set, not the indexes ──

def test_h_reordered_rows_restore_the_same_set(seeded, monkeypatch):
    dlg, gid, ids = seeded
    _select_drawings(dlg, [ids[0], ids[2]])
    before = set(dlg._selected_drawing_ids())

    real_for_symbol = DrawingStore.drawings_for_symbol
    monkeypatch.setattr(
        DrawingStore,
        "drawings_for_symbol",
        staticmethod(lambda symbol: list(reversed(real_for_symbol(symbol)))),
    )

    dlg.reload()

    assert set(dlg._selected_drawing_ids()) == before
    # The list follows the fixture's order; the selection follows identity.
    row_ids = [
        dlg.drawings_list.item(row).data(Qt.ItemDataRole.UserRole)
        for row in range(dlg.drawings_list.count())
    ]
    assert row_ids == list(reversed(ids))


# ── D103 — case (i): the groups table's row selection is independent ───────

def test_i_group_row_selection_does_not_change_drawings_selection(seeded):
    dlg, gid, ids = seeded
    _select_drawings(dlg, ids[:2])
    dlg.groups_table.selectRow(0)
    assert dlg._selected_group_ids() == [gid]

    _toggle_column(dlg, 2)  # Visible

    assert dlg._selected_drawing_ids() == ids[:2]
    # The groups table's own row selection is a different table and is not
    # part of the restore rule: the reload never re-selects it by identity,
    # and nothing in this path touches the drawings selection through it.
