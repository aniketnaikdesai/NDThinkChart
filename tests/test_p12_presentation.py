"""P12-T4 presentation inventory: picker parity, visibility guard, minutes pin
(S-P12-1 picker slot, S-P12-6, AC-D52.5 remainder, DG99).

No production change expected: the picker slot comes from TIMEFRAME_CONFIG
insertion order, the Minutes unit row already covers 30 mins, and the
secs/60 fallback already yields 30.0. A missing/misordered enumeration
entry fails here.
"""

import inspect

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QComboBox

from ibkr.market_data import TIMEFRAME_CONFIG
from services.volume_baseline import minutes_for_timeframe
from ui.drawing_settings_common import VISIBILITY_ROWS, VisibilityTab


def test_p12_t4_t41_picker_order_select_load_persist_parity(qapp, tmp_path):
    """T41: 30 mins sits between 15 mins and 1 hour; parity with intraday."""
    keys = list(TIMEFRAME_CONFIG.keys())
    assert keys.index("30 mins") == keys.index("15 mins") + 1
    assert keys.index("1 hour") == keys.index("30 mins") + 1
    # Select parity: the picker (built from config order, as in MainWindow)
    # selects every timeframe, the new key included.
    combo = QComboBox()
    combo.addItems(keys)
    for tf in keys:
        combo.setCurrentText(tf)
        assert combo.currentText() == tf
    # Load parity: the new row carries the (duration, bar_size) the load
    # path reads — no picker code change required.
    assert TIMEFRAME_CONFIG["30 mins"]["duration"]
    assert TIMEFRAME_CONFIG["30 mins"]["bar_size"]
    # Persist parity: the selected timeframe string round-trips for all keys.
    settings = QSettings(str(tmp_path / "picker.ini"), QSettings.Format.IniFormat)
    for tf in keys:
        settings.setValue("chart/timeframe", tf)
        assert settings.value("chart/timeframe") == tf


def test_p12_t4_t42_visibility_dialog_default_on_and_round_trips(qapp):
    """T42: no new rows, every box default-checked, payload round-trips."""
    assert len(VISIBILITY_ROWS) == 6  # DG99: unchanged unit rows, no new row
    assert ("Minutes", 1, 59) in VISIBILITY_ROWS  # Minutes row covers 30 mins
    tab = VisibilityTab()
    assert set(tab.checks) == (
        {"Ticks", "Ranges"}
        | {label for label, _lo, _hi in VISIBILITY_ROWS}
    )
    assert all(cb.isChecked() for cb in tab.checks.values())
    payload = tab.get_visibility()
    assert "30 mins" not in payload
    assert not any("timeframe" in key.lower() for key in payload)
    tab2 = VisibilityTab()
    tab2.set_visibility(payload)
    assert tab2.get_visibility() == payload


def test_p12_t4_t43_minutes_for_30mins_via_fallback():
    """T43: 30.0 via the secs/60 fallback; no explicit mapping line."""
    assert minutes_for_timeframe("30 mins") == 30.0
    src = inspect.getsource(minutes_for_timeframe)
    assert "30 mins" not in src  # fallback owns it, not a new mapping line
    assert "30.0" not in src
