from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from data.models import Bar


@dataclass
class TickerContext:
    symbol: str
    tick_size: float = 0.01
    digits: int = 2
    prev_close: float = 0.0
    open: float = 0.0


def infer_ticker_context(symbol: str, bars: list[Bar]) -> TickerContext:
    tick_size = 0.25 if symbol.upper().startswith(("/ES", "ES", "/NQ", "NQ")) else 0.01
    digits = 2
    prev_close = bars[-2].close if len(bars) > 1 else (bars[-1].close if bars else 0.0)
    session_open = bars[-1].open if bars else prev_close
    return TickerContext(
        symbol=symbol,
        tick_size=tick_size,
        digits=digits,
        prev_close=prev_close,
        open=session_open,
    )


def _utc_date(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def calculate_rth_gaps(
    bars: list[Bar],
    ticker: TickerContext,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Port of src/services/gapAndVixStudies.ts calculateRthGaps."""
    if len(bars) < 2:
        return []

    params = params or {}
    min_ticks = params.get("minTicks", 1)
    min_gap_size = min_ticks * ticker.tick_size
    max_gaps = params.get("maxGaps", 10)
    extend_bars = params.get("extendBars", 20)
    gaps: list[dict[str, Any]] = []

    def is_new_session(prev: Bar, curr: Bar) -> bool:
        prev_dt = _utc_date(prev.ts)
        curr_dt = _utc_date(curr.ts)
        is_day_diff = prev_dt.date() != curr_dt.date()
        is_time_gap = (curr.ts - prev.ts) >= 14400
        return is_day_diff or is_time_gap

    for i in range(1, len(bars)):
        prev = bars[i - 1]
        curr = bars[i]

        if is_new_session(prev, curr):
            last_close = prev.close
            open_price = curr.open
            top = max(open_price, last_close)
            bottom = min(open_price, last_close)
            gap_diff = top - bottom
            if gap_diff >= min_gap_size and gap_diff > 0:
                gaps.append({
                    "id": f"gap-{curr.ts}-{i}",
                    "isUp": open_price > last_close,
                    "initialTop": top,
                    "initialBottom": bottom,
                    "currentTop": top,
                    "currentBottom": bottom,
                    "openTime": curr.ts,
                    "startBarIndex": i,
                    "lastActiveBarIndex": i,
                    "steps": [{
                        "startBarIndex": i,
                        "endBarIndex": min(len(bars) - 1, i + extend_bars),
                        "top": top,
                        "bottom": bottom,
                    }],
                    "isFullyFilled": False,
                })

        for gap in reversed(gaps):
            if gap["isFullyFilled"] or i <= gap["startBarIndex"]:
                continue

            new_top = gap["currentTop"]
            new_bottom = gap["currentBottom"]
            crossed = False

            if gap["isUp"]:
                if curr.low <= gap["currentBottom"]:
                    crossed = True
                elif curr.low < gap["currentTop"]:
                    new_top = curr.low
            else:
                if curr.high >= gap["currentTop"]:
                    crossed = True
                elif curr.high > gap["currentBottom"]:
                    new_bottom = curr.high

            if crossed:
                gap["isFullyFilled"] = True
                gap["currentTop"] = gap["initialBottom"]
                gap["currentBottom"] = gap["initialBottom"]
                gap["lastActiveBarIndex"] = i
                if gap["steps"]:
                    gap["steps"][-1]["endBarIndex"] = i
                continue

            shrunk = new_top != gap["currentTop"] or new_bottom != gap["currentBottom"]
            gap["currentTop"] = new_top
            gap["currentBottom"] = new_bottom
            gap["lastActiveBarIndex"] = i

            if shrunk and len(gap["steps"]) < 30:
                gap["steps"][-1]["endBarIndex"] = i - 1
                gap["steps"].append({
                    "startBarIndex": i - 1,
                    "endBarIndex": min(len(bars) - 1 + extend_bars, i + extend_bars),
                    "top": new_top,
                    "bottom": new_bottom,
                })
            elif gap["steps"]:
                gap["steps"][-1]["top"] = new_top
                gap["steps"][-1]["bottom"] = new_bottom
                gap["steps"][-1]["endBarIndex"] = len(bars) - 1 + extend_bars

    return [
        gap for gap in gaps
        if not gap["isFullyFilled"] or (len(bars) - 1 - gap["lastActiveBarIndex"]) <= 25
    ][-max_gaps:]


def get_auto_volatility_index(symbol: str) -> dict[str, Any]:
    sym = symbol.upper()
    if "NQ" in sym or "NDX" in sym or "QQQ" in sym:
        return {"symbol": "CBOE:VXN", "name": "VXN", "defaultVol": 20.45}
    if "RTY" in sym or "IWM" in sym:
        return {"symbol": "CBOE:RVX", "name": "RVX", "defaultVol": 22.60}
    if "YM" in sym or "DIA" in sym:
        return {"symbol": "CBOE:VXD", "name": "VXD", "defaultVol": 15.85}
    return {"symbol": "CBOE:VIX", "name": "VIX", "defaultVol": 15.40}


def calculate_vix_standard_deviation(
    ticker: TickerContext,
    bars: list[Bar],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Port of src/services/gapAndVixStudies.ts calculateVixStandardDeviation."""
    params = params or {}
    auto_vol = get_auto_volatility_index(ticker.symbol)
    vol_symbol = params.get("volIndex") or auto_vol["symbol"]
    vol_name = vol_symbol.replace("CBOE:", "")
    vol_value = params.get("customVolValue") or auto_vol["defaultVol"]
    divisor = params.get("sdDivisor") or 15.87

    anchor_price = ticker.prev_close
    anchor_name = "Prev Close"
    if params.get("anchorSource") == "session_open":
        anchor_price = ticker.open
        anchor_name = "Session Open"
    elif bars:
        anchor_price = ticker.prev_close if ticker.prev_close > 0 else bars[0].close
        anchor_name = "Prev RTH Close"

    one_sigma = (anchor_price * vol_value) / divisor / 100.0
    digits = ticker.digits or 2
    levels: list[dict[str, Any]] = []

    if params.get("showAnchor", True):
        levels.append({
            "sigma": 0,
            "price": round(anchor_price, digits),
            "labelFull": f"{vol_name} {vol_value:.2f}  1σ ${one_sigma:.{digits}f} (0σ: {anchor_price:.{digits}f})",
            "labelShort": "0σ",
            "color": params.get("color05", "#94a3b8"),
            "lineStyle": "solid",
            "lineWidth": 1,
        })

    def add_pair(mult: float, color: str, line_style: str, line_width: int) -> None:
        up_price = round(anchor_price + mult * one_sigma, digits)
        dn_price = round(anchor_price - mult * one_sigma, digits)
        sigma_str = f"{mult:g}σ"
        levels.append({
            "sigma": mult,
            "price": up_price,
            "labelFull": f"+{sigma_str} {up_price:.{digits}f}",
            "labelShort": f"+{sigma_str}",
            "color": color,
            "lineStyle": line_style,
            "lineWidth": line_width,
        })
        levels.append({
            "sigma": -mult,
            "price": dn_price,
            "labelFull": f"-{sigma_str} {dn_price:.{digits}f}",
            "labelShort": f"-{sigma_str}",
            "color": color,
            "lineStyle": line_style,
            "lineWidth": line_width,
        })

    if params.get("showSd05", True):
        add_pair(0.5, params.get("color05", "#94a3b8"), "dotted", 1)
    if params.get("showSd1", True):
        add_pair(1.0, params.get("color1", "#38bdf8"), "dashed", 1)
    if params.get("showSd2", True):
        add_pair(2.0, params.get("color2", "#f59e0b"), "dashed", 1)
    if params.get("showSd3", False):
        add_pair(3.0, params.get("color3", "#c084fc"), "solid", 1)

    return {
        "volSymbol": vol_symbol,
        "volValue": vol_value,
        "anchorPrice": anchor_price,
        "anchorName": anchor_name,
        "oneSigmaMove": round(one_sigma, digits),
        "levels": levels,
    }
