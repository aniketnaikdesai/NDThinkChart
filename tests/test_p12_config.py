"""P12-T1 (D52.1): TIMEFRAME_CONFIG gains the 30 mins row.

T11: the new 30 mins row maps to duration 30 D / bar_size 30 mins and sits
between 15 mins and 1 hour (picker order per A140, no picker code change).
T21: the eight pre-existing rows are byte-identical (values and order);
exactly one row is added (len == 9).
"""
from ibkr.market_data import TIMEFRAME_CONFIG

_EXPECTED_CONFIG = {
    "1 min": {"duration": "30 D", "bar_size": "1 min"},
    "5 mins": {"duration": "30 D", "bar_size": "5 mins"},
    "15 mins": {"duration": "30 D", "bar_size": "15 mins"},
    "30 mins": {"duration": "30 D", "bar_size": "30 mins"},
    "1 hour": {"duration": "60 D", "bar_size": "1 hour"},
    "4 hours": {"duration": "60 D", "bar_size": "4 hours"},
    "1 day": {"duration": "1 Y", "bar_size": "1 day"},
    "1 week": {"duration": "2 Y", "bar_size": "1 week"},
    "1 month": {"duration": "10 Y", "bar_size": "1 month"},
}

_EXPECTED_ORDER = [
    "1 min", "5 mins", "15 mins", "30 mins", "1 hour", "4 hours",
    "1 day", "1 week", "1 month",
]

_PREEXISTING = {
    "1 min": {"duration": "30 D", "bar_size": "1 min"},
    "5 mins": {"duration": "30 D", "bar_size": "5 mins"},
    "15 mins": {"duration": "30 D", "bar_size": "15 mins"},
    "1 hour": {"duration": "60 D", "bar_size": "1 hour"},
    "4 hours": {"duration": "60 D", "bar_size": "4 hours"},
    "1 day": {"duration": "1 Y", "bar_size": "1 day"},
    "1 week": {"duration": "2 Y", "bar_size": "1 week"},
    "1 month": {"duration": "10 Y", "bar_size": "1 month"},
}


def test_p12_t1_t11_thirty_min_row_value_and_slot():
    assert TIMEFRAME_CONFIG["30 mins"] == {
        "duration": "30 D",
        "bar_size": "30 mins",
    }
    keys = list(TIMEFRAME_CONFIG.keys())
    assert keys.index("30 mins") == keys.index("15 mins") + 1
    assert keys.index("30 mins") == keys.index("1 hour") - 1


def test_p12_t1_t12_key_order_and_preexisting_rows_unchanged():
    assert list(TIMEFRAME_CONFIG.keys()) == _EXPECTED_ORDER
    assert TIMEFRAME_CONFIG == _EXPECTED_CONFIG
    assert len(TIMEFRAME_CONFIG) == 9
    # Byte-equality of the eight pre-existing rows: exact dicts, exact values.
    for tf, row in _PREEXISTING.items():
        assert TIMEFRAME_CONFIG[tf] == row
        assert set(TIMEFRAME_CONFIG[tf].keys()) == {"duration", "bar_size"}
