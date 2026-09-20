import pytest
import pyqtgraph as pg
from PyQt6.QtWidgets import QPushButton
from data.models import Drawing
from ui.horizontal_line_settings_dialog import HorizontalLineSettingsDialog


def test_horizontal_dialog_has_four_tabs(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                      payload={"y": 7548.85}, color="#38bdf8")
    dlg = HorizontalLineSettingsDialog(drawing)
    labels = [dlg.tabs.tabText(i) for i in range(dlg.tabs.count())]
    assert labels == ["Style", "Text", "Coordinates", "Visibility"]
    # Style tab only exposes the Line swatch (no Extend)
    style_tab = dlg.tabs.widget(0)
    from PyQt6.QtWidgets import QLabel
    qlabels = [l.text() for l in style_tab.findChildren(QLabel)]
    assert "Line" in qlabels
    assert "Extend" not in qlabels
    btn_texts = [b.text() for b in dlg.findChildren(QPushButton)]
    assert not any("Extend" in (t or "") for t in btn_texts)
    dlg.deleteLater()


def test_horizontal_dialog_prefills_single_price(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                      payload={"y": 7548.85}, color="#38bdf8")
    dlg = HorizontalLineSettingsDialog(drawing)
    # Single coordinate (#1 price) only — no bar spinbox
    assert dlg.price.value() == pytest.approx(7548.85)
    assert not hasattr(dlg, "bar1")
    dlg.deleteLater()


def test_horizontal_dialog_update_payload(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                      payload={"y": 7548.85}, color="#38bdf8")
    dlg = HorizontalLineSettingsDialog(drawing)
    dlg.price.setValue(7600.00)
    payload, color = dlg.get_updated_drawing()
    assert payload["y"] == pytest.approx(7600.00)
    assert "text" in payload and "visibility" in payload
    dlg.deleteLater()


def test_horizontal_dialog_text_default_size_12(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                      payload={"y": 100.0})
    dlg = HorizontalLineSettingsDialog(drawing)
    text_tab = dlg.tabs.widget(1)
    assert text_tab.size_combo.currentText() == "12"
    dlg.deleteLater()


def test_horizontal_dialog_visibility_rows(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="horizontal",
                      payload={"y": 100.0})
    dlg = HorizontalLineSettingsDialog(drawing)
    vis = dlg.tabs.widget(3)
    for name in ("Ticks", "Seconds", "Minutes", "Hours", "Days", "Weeks", "Months", "Ranges"):
        assert name in vis.checks
    dlg.deleteLater()
