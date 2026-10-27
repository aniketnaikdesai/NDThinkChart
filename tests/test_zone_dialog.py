import pytest
from PyQt6.QtWidgets import QPushButton
from data.models import Drawing
from ui.zone_settings_dialog import ZoneSettingsDialog

def test_zone_dialog_has_four_tabs_no_extend(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="zone",
                      payload={"x1": 100, "x2": 200, "y1": 101.0, "y2": 105.0},
                      color="#38bdf8")
    dlg = ZoneSettingsDialog(drawing)
    labels = [dlg.tabs.tabText(i) for i in range(dlg.tabs.count())]
    assert labels == ["Style", "Text", "Coordinates", "Visibility"]
    # Extend must not appear anywhere in the dialog
    all_texts = [w.text() for w in dlg.findChildren(QPushButton)]
    assert not any("Extend" in (t or "") for t in all_texts)
    # Style tab has Border, Middle line, Background
    style_tab = dlg.tabs.widget(0)
    from PyQt6.QtWidgets import QLabel, QCheckBox
    qlabels = [l.text() for l in style_tab.findChildren(QLabel)]
    cbs = [c.text() for c in style_tab.findChildren(QCheckBox)]
    assert "Border" in qlabels
    assert "Middle line" in cbs
    assert "Background" in cbs
    dlg.deleteLater()

def test_zone_dialog_prefills_values(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="zone",
                      payload={"x1": 100, "x2": 200, "y1": 101.0, "y2": 105.0},
                      color="#38bdf8")
    dlg = ZoneSettingsDialog(drawing)
    assert dlg.price1.value() == pytest.approx(101.0)
    assert dlg.price2.value() == pytest.approx(105.0)
    assert dlg.bar1.value() == 100
    assert dlg.bar2.value() == 200
    assert dlg.border_swatch.color() == "#38bdf8"
    dlg.deleteLater()

def test_zone_dialog_update_returns_new_payload(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="zone",
                      payload={"x1": 100, "x2": 200, "y1": 101.0, "y2": 105.0},
                      color="#38bdf8")
    dlg = ZoneSettingsDialog(drawing)
    dlg.price1.setValue(102.5)
    dlg.price2.setValue(106.5)
    payload, color = dlg.get_updated_drawing()
    assert payload["y1"] == pytest.approx(102.5)
    assert payload["y2"] == pytest.approx(106.5)
    assert "style" in payload and "text" in payload and "visibility" in payload
    dlg.deleteLater()

def test_zone_visibility_tab_rows(qapp):
    drawing = Drawing(id=1, symbol="TEST", kind="zone",
                      payload={"x1": 100, "x2": 200, "y1": 101.0, "y2": 105.0})
    dlg = ZoneSettingsDialog(drawing)
    vis = dlg.tabs.widget(3)
    for name in ("Ticks", "Seconds", "Minutes", "Hours", "Days", "Weeks", "Months", "Ranges"):
        assert name in vis.checks
    state = vis.get_visibility()
    assert state["Seconds_lo"] == 1 and state["Seconds_hi"] == 59
    assert state["Days_hi"] == 366
    assert state["Weeks_hi"] == 52
    assert state["Months_hi"] == 12
    dlg.deleteLater()

