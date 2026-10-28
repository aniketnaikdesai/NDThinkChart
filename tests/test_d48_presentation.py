"""P8-T04 presentation remainder: daily+ predicate sweep, picker parity,
burst minutes, visibility guard (S-P8-4 half, S-P8-6, S-P8-7, DG97, R95,
AC-D48.4 bands half, AC-D48.5).
"""

from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QComboBox

from data.bar_aggregator import TIMEFRAME_SECONDS
from ibkr.market_data import TIMEFRAME_CONFIG
from services.session_service import session_bands, session_bands_for_range
from services.time_collapse_service import (
    build_collapse_map,
    is_daily_or_coarser,
)
from services.volume_baseline import minutes_for_timeframe
from ui.drawing_settings_common import VISIBILITY_ROWS, VisibilityTab
from ui.lwc_view import session_regions

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")

NEW_TIMEFRAMES = ("1 week", "1 month")


def _et_ts(y, mo, d, h=12, mi=0):
    from datetime import datetime

    return int(datetime(y, mo, d, h, mi, tzinfo=_EASTERN).timestamp())


def _bars(*ts_list):
    return [SimpleNamespace(ts=ts) for ts in ts_list]


# Monday 2026-10-26 midday ET + two following days (identity-branch inputs;
# no collapse is computed on this branch, so any ordered ts triple works).
_DAY_TS = (
    _et_ts(2026, 10, 26, 12),
    _et_ts(2026, 10, 27, 12),
    _et_ts(2026, 10, 28, 12),
)


def test_p8_t04_t11_bands_collapse_regions_absent_for_new_timeframes():
    """T11: no bands, identity collapse, no session regions for 1w/1m."""
    for tf in ("1 day", *NEW_TIMEFRAMES):
        assert session_bands(_bars(*_DAY_TS), tf) == []
        assert session_bands_for_range(_DAY_TS[0], _DAY_TS[-1], tf) == []
        for ext_hours in (False, True):
            cmap = build_collapse_map(_bars(*_DAY_TS), tf, ext_hours)
            assert cmap.is_identity
            assert cmap.x_values == list(_DAY_TS)
            for ts in _DAY_TS:
                assert cmap.to_display(ts) == ts
                assert cmap.to_ts(ts) == ts
            # Tail-step keeps the identity branch for the new keys too.
            assert cmap.extend(_DAY_TS[-1] + TIMEFRAME_SECONDS[tf]) is True
            assert cmap.x_values[-1] == _DAY_TS[-1] + TIMEFRAME_SECONDS[tf]
        bars = _bars(*_DAY_TS)
        assert session_regions(bars, bars, tf, True) == []
        assert session_regions(bars, bars, tf, False) == []
    # The shared predicate is selective: intraday keeps bands + collapse.
    assert is_daily_or_coarser("1 day")
    assert is_daily_or_coarser("1 week")
    assert is_daily_or_coarser("1 month")
    assert not is_daily_or_coarser("1 hour")
    assert not is_daily_or_coarser("5 mins")
    monday_bands = session_bands_for_range(
        _et_ts(2026, 10, 26, 0), _et_ts(2026, 10, 26, 23, 59), "1 hour")
    assert len(monday_bands) == 2  # pre + post session bands survive
    fri = _et_ts(2026, 10, 23, 15)
    mon = _et_ts(2026, 10, 26, 9, 30)
    weekend_map = build_collapse_map(_bars(fri, mon), "1 hour", False)
    assert not weekend_map.is_identity  # weekend gap still collapses


def test_p8_t04_t21_burst_minutes_for_new_timeframes():
    """T21: explicit RTH-session minutes; nominal secs/60 would fail."""
    assert minutes_for_timeframe("1 day") == 390.0  # precedent kept
    assert minutes_for_timeframe("1 week") == 1950.0
    assert minutes_for_timeframe("1 month") == 8190.0
    assert TIMEFRAME_SECONDS["1 week"] / 60.0 != 1950.0
    assert TIMEFRAME_SECONDS["1 month"] / 60.0 != 8190.0


def test_p8_t04_t31_picker_order_select_load_persist_parity(qapp, tmp_path):
    """T31: 1w/1m follow 1 day; select/load/persist like every timeframe."""
    keys = list(TIMEFRAME_CONFIG.keys())
    day_idx = keys.index("1 day")
    assert keys[day_idx + 1] == "1 week"
    assert keys[day_idx + 2] == "1 month"
    # Select parity: the picker (built from config order, as in MainWindow)
    # selects every timeframe, new keys included.
    combo = QComboBox()
    combo.addItems(keys)
    for tf in keys:
        combo.setCurrentText(tf)
        assert combo.currentText() == tf
    # Load parity: every row carries the (duration, bar_size) the load path
    # reads — no picker code change required.
    for tf in NEW_TIMEFRAMES:
        assert TIMEFRAME_CONFIG[tf]["duration"]
        assert TIMEFRAME_CONFIG[tf]["bar_size"]
    # Persist parity: the selected timeframe string round-trips for all keys.
    settings = QSettings(str(tmp_path / "picker.ini"), QSettings.Format.IniFormat)
    for tf in keys:
        settings.setValue("chart/timeframe", tf)
        assert settings.value("chart/timeframe") == tf


def test_p8_t04_t41_visibility_dialog_default_on_and_round_trips(qapp):
    """T41: no new rows, every box default-checked, payload round-trips."""
    assert len(VISIBILITY_ROWS) == 6  # DG97: unchanged unit rows, no new row
    tab = VisibilityTab()
    assert set(tab.checks) == (
        {"Ticks", "Ranges"}
        | {label for label, _lo, _hi in VISIBILITY_ROWS}
    )
    assert all(cb.isChecked() for cb in tab.checks.values())
    payload = tab.get_visibility()
    assert "1 week" not in payload and "1 month" not in payload
    assert not any("timeframe" in key.lower() for key in payload)
    tab2 = VisibilityTab()
    tab2.set_visibility(payload)
    assert tab2.get_visibility() == payload
