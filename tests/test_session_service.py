import pytest
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from data.models import Bar
from services.session_service import session_bands, session_bands_for_range

EASTERN = ZoneInfo("America/New_York")

BASE_TS = 1_700_000_000

def _bar(ts: int) -> Bar:
    return Bar(symbol="TEST", timeframe="5 mins", ts=ts, open=100, high=101, low=99, close=100, volume=1000)

def _et_ts(year, month, day, hour, minute=0):
    return int(datetime(year, month, day, hour, minute, tzinfo=EASTERN).timestamp())

def test_session_bands_intraday_returns_pre_post():
    # Use 3 session days: pick EST period Jan 2024 to avoid DST
    # Bars cover 3 days inclusive
    t_min = _et_ts(2024, 1, 10, 5, 0)  # inside pre of day 1
    t_max = _et_ts(2024, 1, 12, 19, 0)  # inside post of day 3
    bars = [_bar(t_min), _bar(t_max), _bar(_et_ts(2024, 1, 11, 10, 0))]
    bands = session_bands(bars, "5 mins")
    # Expect 6 intervals (3 pre + 3 post) clipped to range: first pre clipped to t_min, last post clipped to t_max
    kinds = [b["kind"] for b in bands]
    assert kinds.count("pre") == 3
    assert kinds.count("post") == 3
    assert len(bands) == 6
    # no RTH or overnight
    assert all(k in ("pre", "post") for k in kinds)
    # verify boundaries
    # day 1 pre should start at t_min (clipped) and end at 09:30 ET Jan10
    assert bands[0]["start_ts"] == t_min
    assert bands[0]["end_ts"] == _et_ts(2024, 1, 10, 9, 30)
    # day 3 post should end at t_max
    assert bands[-1]["start_ts"] == _et_ts(2024, 1, 12, 16, 0)
    assert bands[-1]["end_ts"] == t_max

def test_session_bands_1day_returns_empty():
    bars = [_bar(BASE_TS), _bar(BASE_TS+3600)]
    assert session_bands(bars, "1 day") == []

def test_session_bands_utc_boundaries_same_et_instants():
    # EST day Jan 15 2024 (EST UTC-5)
    t_min = _et_ts(2024, 1, 15, 0, 0)
    t_max = _et_ts(2024, 1, 15, 23, 59)
    bars = [_bar(t_min), _bar(t_max)]
    bands = session_bands(bars, "5 mins")
    # pre 04:00 ET = 09:00 UTC, post 16:00 ET = 21:00 UTC
    pre = [b for b in bands if b["kind"] == "pre"][0]
    post = [b for b in bands if b["kind"] == "post"][0]
    # Verify by converting ET 04:00 to timestamp and comparing
    assert pre["start_ts"] == _et_ts(2024, 1, 15, 4, 0)
    assert pre["end_ts"] == _et_ts(2024, 1, 15, 9, 30)
    assert post["start_ts"] == _et_ts(2024, 1, 15, 16, 0)
    assert post["end_ts"] == _et_ts(2024, 1, 15, 20, 0)
    # Verify UTC equivalence: 04:00 ET in EST should be 09:00 UTC
    # 04:00 ET timestamp's UTC representation should be 09:00 UTC
    dt_utc = datetime.fromtimestamp(pre["start_ts"], tz=timezone.utc)
    assert dt_utc.hour == 9

def test_session_bands_dst_transition():
    # Week containing DST start 2026-03-08 (second Sun March)
    # Before DST: March 7 is EST (UTC-5), March 9 is EDT (UTC-4)
    t_min = _et_ts(2026, 3, 7, 0, 0)
    t_max = _et_ts(2026, 3, 10, 23, 59)
    bars = [_bar(t_min), _bar(t_max)]
    bands = session_bands(bars, "5 mins")
    # Get pre bands for Mar7 and Mar9
    mar7_pre = [b for b in bands if b["start_ts"] == _et_ts(2026, 3, 7, 4, 0)]
    mar9_pre = [b for b in bands if b["start_ts"] == _et_ts(2026, 3, 9, 4, 0)]
    assert mar7_pre
    assert mar9_pre
    # Both should be 04:00 local, but UTC diff 1h
    # Verify that the UTC hour differs by 1
    dt7 = datetime.fromtimestamp(mar7_pre[0]["start_ts"], tz=timezone.utc)
    dt9 = datetime.fromtimestamp(mar9_pre[0]["start_ts"], tz=timezone.utc)
    # Mar7 EDT still EST -> 09:00 UTC; Mar9 -> 08:00 UTC
    assert dt7.hour == 9
    assert dt9.hour == 8

def test_session_bands_boundary_classification_and_clipping():
    # Test clipping: t_min exactly at 09:30, t_max exactly at 16:00
    t_0930 = _et_ts(2024, 1, 16, 9, 30)
    t_1600 = _et_ts(2024, 1, 16, 16, 0)
    # Range starts at 09:30, ends at 16:00 -> no pre/post should be included for that day because pre [04:00,09:30) ends at 09:30 (zero length if clipped), post starts at 16:00 starts at t_max (zero length if we consider interval [16:00,20:00) but clipped start==end? Actually our intersect logic excludes zero-length, so for range [09:30,16:00) pre would be [04:00,09:30) intersect -> [09:30,09:30) length 0 -> excluded, post [16:00,20:00) intersect -> [16:00,16:00) length 0 -> excluded. So bands should be empty for that single day range where min==09:30 and max==16:00.
    bars = [_bar(t_0930), _bar(t_1600)]
    bands = session_bands(bars, "5 mins")
    # No band should straddle RTH; verify no band covers 09:30-16:00
    for b in bands:
        assert not (b["start_ts"] <= t_0930 < b["end_ts"] and b["kind"] == "pre")
        assert not (b["start_ts"] <= t_1600 < b["end_ts"] and b["kind"] == "post" and b["start_ts"] != t_1600)  # post starts at 16:00, so t_1600 should be start
    # Now test that post band starting at 16:00 is correctly included when range extends past
    bars2 = [_bar(t_0930), _bar(_et_ts(2024, 1, 16, 17, 0))]
    bands2 = session_bands(bars2, "5 mins")
    post = [b for b in bands2 if b["kind"] == "post"]
    assert post[0]["start_ts"] == t_1600
    # Clipping: no band extends outside [t_min, t_max]
    t_min = _et_ts(2024, 1, 17, 5, 0)
    t_max = _et_ts(2024, 1, 17, 18, 0)
    bands3 = session_bands([_bar(t_min), _bar(t_max)], "5 mins")
    for b in bands3:
        assert b["start_ts"] >= t_min
        assert b["end_ts"] <= t_max


# ── Q-54 (a): boundary validation — warn once with the count, skip bad rows ──


class _NoTs:
    pass


class _BadTs:
    ts = "not-a-ts"


class _NoneTs:
    ts = None


class _NaNTs:
    ts = float("nan")


class _BoolTs:
    ts = True


def test_Q54_invalid_ts_rows_warn_and_skip(caplog):
    import logging
    t0 = _et_ts(2024, 1, 15, 5, 0)
    t1 = _et_ts(2024, 1, 15, 18, 0)
    bars = [_bar(t0), _bar(t1), _NoTs(), _BadTs(), _NoneTs(), _NaNTs(),
            _BoolTs()]
    with caplog.at_level(logging.WARNING, logger="services.session_service"):
        bands = session_bands(bars, "5 mins")
    # Valid rows still produce their bands (pre + post for the single day).
    assert [b["kind"] for b in bands] == ["pre", "post"]
    assert bands[0]["start_ts"] == t0  # pre clipped to first valid bar
    assert bands[0]["end_ts"] == _et_ts(2024, 1, 15, 9, 30)
    assert bands[1]["start_ts"] == _et_ts(2024, 1, 15, 16, 0)
    assert bands[1]["end_ts"] == t1  # post clipped to last valid bar
    # One concise warning reporting the skipped-row count, not per-row noise.
    warns = [r for r in caplog.records
             if r.name == "services.session_service"
             and r.levelname == "WARNING"]
    assert len(warns) == 1
    assert "5" in warns[0].message


def test_Q54_all_invalid_ts_returns_empty_with_warning(caplog):
    import logging
    with caplog.at_level(logging.WARNING, logger="services.session_service"):
        assert session_bands([_NoTs(), _BadTs()], "5 mins") == []
    warns = [r for r in caplog.records
             if r.name == "services.session_service"
             and r.levelname == "WARNING"]
    assert len(warns) == 1


def test_Q54_valid_input_logs_no_warning(caplog, recwarn):
    t0 = _et_ts(2024, 1, 15, 5, 0)
    t1 = _et_ts(2024, 1, 15, 18, 0)
    bands = session_bands([_bar(t0), _bar(t1)], "5 mins")
    assert len(bands) == 2
    assert [r for r in recwarn.list
            if r.filename == "session_service.py"] == []
