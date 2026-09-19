"""Tests for ui/studies_dialog.py — grouped rows and color swatches."""

import pytest

from ui.studies_dialog import StudyRow, StudiesDialog, DEFAULT_STUDIES


@pytest.fixture(autouse=True)
def _qt_app(qapp):
    return qapp


def study(**overrides):
    base = {
        "type": "test", "label": "Test Study", "enabled": False,
        "params": {"period": 20, "source": "close", "color": "#f59e0b"},
    }
    base.update(overrides)
    return base


class TestStudyRow:
    def test_get_config_round_trip(self):
        row = StudyRow(study())
        cfg = row.get_config()
        assert cfg["enabled"] is False
        assert cfg["params"]["period"] == 20
        assert cfg["params"]["color"] == "#f59e0b"

    def test_enabled_from_group_checkbox(self):
        row = StudyRow(study())
        row.group.setChecked(True)
        assert row.get_config()["enabled"] is True

    def test_changed_param_is_captured(self):
        row = StudyRow(study())
        row._param_widgets["period"].setValue(55)
        assert row.get_config()["params"]["period"] == 55

    def test_color_swatch_created_and_defaults(self):
        row = StudyRow(study())
        swatch = row._color_widgets["color"]
        assert swatch.toolTip() == "#f59e0b"

    def test_bool_params_use_checkbox(self):
        row = StudyRow(study(params={"showSd1": True, "color": "#123456"}))
        assert row.get_config()["params"]["showSd1"] is True

    def test_ict_advanced_params_exposed(self):
        ict_cfg = next(s for s in DEFAULT_STUDIES if s["type"] == "ict")
        row = StudyRow(ict_cfg)
        assert "showKillzones" in row._param_widgets
        assert "cMSSBull" in row._color_widgets

    def test_vix_color_swatches_exposed(self):
        vix_cfg = next(s for s in DEFAULT_STUDIES if s["type"] == "vix_sd")
        row = StudyRow(vix_cfg)
        assert "color1" in row._color_widgets
        assert "color3" in row._color_widgets


class TestStudiesDialog:
    def test_apply_emits_full_config_list(self, qapp):
        dialog = StudiesDialog()
        emitted = []
        dialog.studies_changed.connect(emitted.append)
        dialog._apply()
        assert len(emitted) == 1
        assert len(emitted[0]) == len(DEFAULT_STUDIES)
        assert {cfg["type"] for cfg in emitted[0]} == {s["type"] for s in DEFAULT_STUDIES}

    def test_preserves_study_colors(self, qapp):
        dialog = StudiesDialog()
        emitted = []
        dialog.studies_changed.connect(emitted.append)
        dialog._apply()
        vix = next(c for c in emitted[0] if c["type"] == "vix_sd")
        assert vix["params"]["color1"] == "#38bdf8"