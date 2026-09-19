from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from data.models import Bar
from services.gap_vix_service import TickerContext


def _atr(bars: list[Bar], period: int = 10) -> list[float]:
    trs: list[float] = []
    for i, bar in enumerate(bars):
        if i == 0:
            trs.append(bar.high - bar.low)
        else:
            trs.append(max(
                bar.high - bar.low,
                abs(bar.high - bars[i - 1].close),
                abs(bar.low - bars[i - 1].close),
            ))
    result: list[float] = []
    total = 0.0
    for i, tr in enumerate(trs):
        total += tr
        if i < period:
            result.append(total / (i + 1))
        else:
            total -= trs[i - period]
            result.append(total / period)
    return result


def _mean_body(bars: list[Bar], length: int) -> list[float]:
    bodies = [abs(bar.close - bar.open) for bar in bars]
    result: list[float] = []
    total = 0.0
    for i, body in enumerate(bodies):
        total += body
        if i < length:
            result.append(total / (i + 1))
        else:
            total -= bodies[i - length]
            result.append(total / length)
    return result


def _utc_dt(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def calculate_ict_concepts(
    bars: list[Bar],
    ticker: TickerContext,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Python port of src/services/ictStudies.ts calculateIctConcepts."""
    n = len(bars)
    if n < 10:
        return _empty_result()

    params = params or {}
    show_ms = params.get("showMS", True)
    ms_length = max(3, min(10, params.get("msLength", 5)))
    show_mss = params.get("showMSS", True)
    show_bos = params.get("showBOS", True)
    c_mss_bull = params.get("cMSSBull", "#00e6a1")
    c_mss_bear = params.get("cMSSBear", "#e60400")
    c_bos_bull = params.get("cBOSBull", "#00e6a1")
    c_bos_bear = params.get("cBOSBear", "#e60400")

    show_ob = params.get("showOB", True)
    ob_length = max(3, params.get("obLength", 10))
    show_bull_ob = params.get("showBullOB", 2)
    show_bear_ob = params.get("showBearOB", 2)
    use_body = params.get("useBody", True)
    c_bull_ob = params.get("cBullOB", "#3e89fa")
    c_bull_break = params.get("cBullBreak", "rgba(71, 133, 249, 0.45)")
    c_bear_ob = params.get("cBearOB", "#ff3131")
    c_bear_break = params.get("cBearBreak", "rgba(249, 255, 87, 0.45)")

    show_fvg = params.get("showFVG", True)
    show_bpr = params.get("showBPR", True)
    max_fvgs = max(1, min(15, params.get("maxFVGs", 3)))
    c_fvg_bull = params.get("cFVGBull", "#00e676")
    c_fvg_bear = params.get("cFVGBear", "#ff5252")

    show_liquidity = params.get("showLiquidity", True)
    liq_margin = params.get("liqMargin", 2.5)
    max_liq_boxes = params.get("maxLiqBoxes", 2)
    c_liq_buy = params.get("cLiqBuy", "#fa451c")
    c_liq_sell = params.get("cLiqSell", "#1ce4fa")

    show_vi = params.get("showVI", True)
    max_vi = params.get("maxVI", 2)
    c_vi = params.get("cVI", "#06b2d0")

    show_nwog = params.get("showNWOG", True)
    show_ndog = params.get("showNDOG", True)
    c_nwog = params.get("cNWOG", "#ff5252")
    c_ndog = params.get("cNDOG", "#ff9800")

    show_displacement = params.get("showDisplacement", False)
    perc_body = params.get("bodyThreshold", 0.36)
    show_killzones = params.get("showKillzones", False)

    atrs = _atr(bars, 10)
    mean_bodies = _mean_body(bars, ms_length)

    pivot_highs, pivot_lows = _pivots(bars, ms_length)
    market_structures, current_dir = _market_structures(
        bars, pivot_highs, pivot_lows, show_ms, show_mss, show_bos,
        c_mss_bull, c_mss_bear, c_bos_bull, c_bos_bear, ticker.tick_size,
    )
    order_blocks = _order_blocks(
        bars, show_ob, ob_length, use_body, c_bull_ob, c_bull_break,
        c_bear_ob, c_bear_break, show_bull_ob, show_bear_ob,
    )
    fvgs, displacements = _fair_value_gaps(
        bars, mean_bodies, show_fvg, show_bpr, max_fvgs,
        c_fvg_bull, c_fvg_bear, show_displacement, perc_body,
    )
    liquidity_pools = _liquidity_pools(
        bars, pivot_highs, pivot_lows, atrs, show_liquidity,
        liq_margin, max_liq_boxes, c_liq_buy, c_liq_sell,
    )
    volume_imbalances = _volume_imbalances(bars, show_vi, max_vi, c_vi)
    opening_gaps = _opening_gaps(bars, ticker, show_nwog, show_ndog, c_nwog, c_ndog)
    killzones = _killzones(
        bars,
        show_killzones,
        params.get("showNYKZ", True),
        params.get("showLondonOpenKZ", True),
        params.get("showLondonCloseKZ", True),
        params.get("showAsianKZ", True),
    )

    bias = "Bullish" if current_dir == 1 else "Bearish" if current_dir == -1 else "Neutral"
    fvg_count = len([fvg for fvg in fvgs if not fvg["isBroken"]])
    ob_count = len(order_blocks)
    summary = f"ICT [{bias} • {fvg_count} FVG • {ob_count} OB]"

    return {
        "marketStructures": market_structures,
        "orderBlocks": order_blocks,
        "fairValueGaps": fvgs,
        "liquidityPools": liquidity_pools,
        "volumeImbalances": volume_imbalances,
        "openingGaps": opening_gaps,
        "displacements": displacements,
        "killzones": killzones,
        "currentBias": bias,
        "summaryBadge": summary,
    }


def _empty_result() -> dict[str, Any]:
    return {
        "marketStructures": [],
        "orderBlocks": [],
        "fairValueGaps": [],
        "liquidityPools": [],
        "volumeImbalances": [],
        "openingGaps": [],
        "displacements": [],
        "killzones": [],
        "currentBias": "Neutral",
        "summaryBadge": "ICT [Neutral]",
    }


def _pivots(bars: list[Bar], length: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    highs: list[dict[str, Any]] = []
    lows: list[dict[str, Any]] = []
    for i in range(length, len(bars) - length):
        cur_h = bars[i].high
        cur_l = bars[i].low
        is_high = True
        is_low = True
        for j in range(1, length + 1):
            if bars[i - j].high >= cur_h or bars[i + j].high > cur_h:
                is_high = False
            if bars[i - j].low <= cur_l or bars[i + j].low < cur_l:
                is_low = False
        if is_high:
            highs.append({"index": i, "price": cur_h})
        if is_low:
            lows.append({"index": i, "price": cur_l})
    return highs, lows


def _market_structures(
    bars: list[Bar],
    pivot_highs: list[dict[str, Any]],
    pivot_lows: list[dict[str, Any]],
    show_ms: bool,
    show_mss: bool,
    show_bos: bool,
    c_mss_bull: str,
    c_mss_bear: str,
    c_bos_bull: str,
    c_bos_bear: str,
    tick_size: float,
) -> tuple[list[dict[str, Any]], int]:
    structures: list[dict[str, Any]] = []
    current_dir = 0
    last_high = None
    last_low = None
    combined = sorted(
        [{**p, "dir": 1} for p in pivot_highs] + [{**p, "dir": -1} for p in pivot_lows],
        key=lambda p: p["index"],
    )

    if not show_ms:
        return structures, current_dir

    for idx, pivot in enumerate(combined):
        if pivot["dir"] == 1:
            last_high = pivot
        else:
            last_low = pivot
        next_idx = combined[idx + 1]["index"] if idx < len(combined) - 1 else len(bars) - 1
        for bar_idx in range(pivot["index"] + 1, next_idx + 1):
            bar = bars[bar_idx]
            if last_high and bar.close > last_high["price"] and current_dir < 1:
                current_dir = 1
                if show_mss:
                    structures.append(_structure("mss-bull", "MSS", "bullish", last_high, bar_idx, bars, c_mss_bull))
            elif last_low and bar.close < last_low["price"] and current_dir > -1:
                current_dir = -1
                if show_mss:
                    structures.append(_structure("mss-bear", "MSS", "bearish", last_low, bar_idx, bars, c_mss_bear))
            elif show_bos and current_dir == 1 and last_high and bar.close > last_high["price"]:
                last_line = structures[-1] if structures else None
                if not last_line or abs(last_line["price"] - last_high["price"]) > tick_size * 0.5:
                    structures.append(_structure("bos-bull", "BOS", "bullish", last_high, bar_idx, bars, c_bos_bull))
            elif show_bos and current_dir == -1 and last_low and bar.close < last_low["price"]:
                last_line = structures[-1] if structures else None
                if not last_line or abs(last_line["price"] - last_low["price"]) > tick_size * 0.5:
                    structures.append(_structure("bos-bear", "BOS", "bearish", last_low, bar_idx, bars, c_bos_bear))

    return structures, current_dir


def _structure(prefix: str, stype: str, direction: str, swing: dict[str, Any], end_idx: int, bars: list[Bar], color: str) -> dict[str, Any]:
    return {
        "id": f"{prefix}-{end_idx}",
        "type": stype,
        "direction": direction,
        "price": swing["price"],
        "startIndex": swing["index"],
        "endIndex": end_idx,
        "startTime": bars[swing["index"]].ts,
        "endTime": bars[end_idx].ts,
        "color": color,
    }


def _order_blocks(
    bars: list[Bar],
    show_ob: bool,
    ob_length: int,
    use_body: bool,
    c_bull_ob: str,
    c_bull_break: str,
    c_bear_ob: str,
    c_bear_break: str,
    show_bull_ob: int,
    show_bear_ob: int,
) -> list[dict[str, Any]]:
    if not show_ob:
        return []
    bullish: list[dict[str, Any]] = []
    bearish: list[dict[str, Any]] = []
    n = len(bars)
    for i in range(ob_length, n - 1):
        ch = bars[i].high
        cl = bars[i].low
        is_top = all(bars[i - j].high <= ch for j in range(1, ob_length + 1))
        is_bottom = all(bars[i - j].low >= cl for j in range(1, ob_length + 1))
        if is_top:
            for k in range(i + 1, min(n, i + 35)):
                if bars[k].close > ch:
                    lowest_idx = min(range(i, k), key=lambda m: bars[m].low)
                    bullish.insert(0, _ob("ob-bull", "bullish", lowest_idx, bars, use_body, c_bull_ob, c_bull_break))
                    break
        if is_bottom:
            for k in range(i + 1, min(n, i + 35)):
                if bars[k].close < cl:
                    highest_idx = max(range(i, k), key=lambda m: bars[m].high)
                    bearish.insert(0, _ob("ob-bear", "bearish", highest_idx, bars, use_body, c_bear_ob, c_bear_break))
                    break

    for ob in bullish:
        for bar_idx in range(ob["barIndex"] + 1, n):
            if min(bars[bar_idx].close, bars[bar_idx].open) < ob["bottom"]:
                ob["isBreaker"] = True
                ob["breakTime"] = bars[bar_idx].ts
                break
    for ob in bearish:
        for bar_idx in range(ob["barIndex"] + 1, n):
            if max(bars[bar_idx].close, bars[bar_idx].open) > ob["top"]:
                ob["isBreaker"] = True
                ob["breakTime"] = bars[bar_idx].ts
                break

    return bullish[:show_bull_ob] + bearish[:show_bear_ob]


def _ob(prefix: str, direction: str, idx: int, bars: list[Bar], use_body: bool, color: str, break_color: str) -> dict[str, Any]:
    bar = bars[idx]
    return {
        "id": f"{prefix}-{idx}",
        "direction": direction,
        "top": max(bar.open, bar.close) if use_body else bar.high,
        "bottom": min(bar.open, bar.close) if use_body else bar.low,
        "barIndex": idx,
        "time": bar.ts,
        "isBreaker": False,
        "color": color,
        "breakColor": break_color,
    }


def _fair_value_gaps(
    bars: list[Bar],
    mean_bodies: list[float],
    show_fvg: bool,
    show_bpr: bool,
    max_fvgs: int,
    c_bull: str,
    c_bear: str,
    show_displacement: bool,
    perc_body: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bull: list[dict[str, Any]] = []
    bear: list[dict[str, Any]] = []
    displacements: list[dict[str, Any]] = []
    n = len(bars)

    for i in range(2, n):
        c0, c1, c2 = bars[i], bars[i - 1], bars[i - 2]
        body = abs(c1.close - c1.open)
        mx = max(c1.close, c1.open)
        mn = min(c1.close, c1.open)
        small_upper = (c1.high - mx) < body * perc_body
        small_lower = (mn - c1.low) < body * perc_body
        is_displacement = body > mean_bodies[i - 1] and small_upper and small_lower
        if show_displacement and is_displacement:
            displacements.append({
                "barIndex": i - 1,
                "time": c1.ts,
                "direction": "up" if c1.close > c1.open else "down",
                "price": c1.low if c1.close > c1.open else c1.high,
            })

        if show_fvg and c0.low > c2.high and c1.close > c1.open:
            fvg = _fvg("fvg-bull", i, "bullish", c0.low, c2.high, bars, c_bull)
            if fvg:
                _mark_fvg_state(fvg, bars, i, "bullish")
                bull.insert(0, fvg)
        if show_fvg and c0.high < c2.low and c1.close < c1.open:
            fvg = _fvg("fvg-bear", i, "bearish", c2.low, c0.high, bars, c_bear)
            if fvg:
                _mark_fvg_state(fvg, bars, i, "bearish")
                bear.insert(0, fvg)

    bprs: list[dict[str, Any]] = []
    if show_bpr and bull and bear:
        latest_bull, latest_bear = bull[0], bear[0]
        overlap_top = min(latest_bull["top"], latest_bear["top"])
        overlap_bottom = max(latest_bull["bottom"], latest_bear["bottom"])
        if overlap_top > overlap_bottom:
            bprs.append({
                "id": f"bpr-overlap-{latest_bull['id']}-{latest_bear['id']}",
                "type": "BPR",
                "direction": "bullish" if latest_bull["startIndex"] > latest_bear["startIndex"] else "bearish",
                "top": overlap_top,
                "bottom": overlap_bottom,
                "startIndex": min(latest_bull["startIndex"], latest_bear["startIndex"]),
                "endIndex": max(latest_bull["endIndex"], latest_bear["endIndex"]),
                "startTime": min(latest_bull["startTime"], latest_bear["startTime"]),
                "color": "#f59e0b",
                "isMitigated": latest_bull["isMitigated"] or latest_bear["isMitigated"],
                "isBroken": latest_bull["isBroken"] and latest_bear["isBroken"],
            })

    return bprs + bull[:max_fvgs] + bear[:max_fvgs], displacements


def _fvg(prefix: str, idx: int, direction: str, top: float, bottom: float, bars: list[Bar], color: str) -> dict[str, Any] | None:
    if top <= bottom:
        return None
    return {
        "id": f"{prefix}-{idx}",
        "type": "FVG",
        "direction": direction,
        "top": top,
        "bottom": bottom,
        "startIndex": idx - 2,
        "endIndex": min(len(bars) - 1, idx + 12),
        "startTime": bars[idx - 2].ts,
        "color": color,
        "isMitigated": False,
        "isBroken": False,
    }


def _mark_fvg_state(fvg: dict[str, Any], bars: list[Bar], idx: int, direction: str) -> None:
    for k in range(idx + 1, len(bars)):
        if direction == "bullish":
            if bars[k].low < fvg["top"]:
                fvg["isMitigated"] = True
            if bars[k].close < fvg["bottom"]:
                fvg["isBroken"] = True
                break
        else:
            if bars[k].high > fvg["bottom"]:
                fvg["isMitigated"] = True
            if bars[k].close > fvg["top"]:
                fvg["isBroken"] = True
                break


def _liquidity_pools(
    bars: list[Bar],
    pivot_highs: list[dict[str, Any]],
    pivot_lows: list[dict[str, Any]],
    atrs: list[float],
    show: bool,
    margin_factor: float,
    max_boxes: int,
    buy_color: str,
    sell_color: str,
) -> list[dict[str, Any]]:
    if not show:
        return []
    pools: list[dict[str, Any]] = []
    for pivots, ptype, color in ((pivot_highs, "buyside", buy_color), (pivot_lows, "sellside", sell_color)):
        if len(pivots) <= 2:
            continue
        count_for_type = 0
        for i, p1 in enumerate(pivots[:-1]):
            margin = (atrs[p1["index"]] or 2) / margin_factor
            cluster = [p for p in pivots[i:] if abs(p["price"] - p1["price"]) <= margin]
            if len(cluster) >= 2:
                min_p = min(p["price"] for p in cluster)
                max_p = max(p["price"] for p in cluster)
                avg_p = (min_p + max_p) / 2
                top = avg_p + margin
                bottom = avg_p - margin
                start_idx = p1["index"]
                swept = any(bar.high > top for bar in bars[start_idx + 1:]) if ptype == "buyside" else any(bar.low < bottom for bar in bars[start_idx + 1:])
                pools.append({
                    "id": f"{'bsl' if ptype == 'buyside' else 'ssl'}-{start_idx}",
                    "type": ptype,
                    "top": top,
                    "bottom": bottom,
                    "levelPrice": avg_p,
                    "startIndex": start_idx,
                    "startTime": bars[start_idx].ts,
                    "isSwept": swept,
                    "color": color,
                })
                count_for_type += 1
                if count_for_type >= max_boxes:
                    break
    return pools


def _volume_imbalances(bars: list[Bar], show: bool, max_vi: int, color: str) -> list[dict[str, Any]]:
    if not show:
        return []
    vis: list[dict[str, Any]] = []
    for i in range(1, len(bars)):
        cur, prev = bars[i], bars[i - 1]
        cur_mn, cur_mx = min(cur.close, cur.open), max(cur.close, cur.open)
        prev_mn, prev_mx = min(prev.close, prev.open), max(prev.close, prev.open)
        bull = cur.open > prev.close and prev.high > cur.low and cur.close > prev.close and cur.open > prev.open and prev.high < cur_mn
        bear = cur.open < prev.close and prev.low < cur.high and cur.close < prev.close and cur.open < prev.open and prev.low > cur_mx
        if bull:
            vis.insert(0, {"id": f"vi-bull-{i}", "direction": "bullish", "top": cur_mn, "bottom": prev_mx, "barIndex": i, "time": cur.ts, "color": color})
        elif bear:
            vis.insert(0, {"id": f"vi-bear-{i}", "direction": "bearish", "top": prev_mn, "bottom": cur_mx, "barIndex": i, "time": cur.ts, "color": color})
    return vis[:max_vi]


def _opening_gaps(bars: list[Bar], ticker: TickerContext, show_nwog: bool, show_ndog: bool, nwog_color: str, ndog_color: str) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for i in range(1, len(bars)):
        prev_dt = _utc_dt(bars[i - 1].ts)
        cur_dt = _utc_dt(bars[i].ts)
        if show_nwog and prev_dt.weekday() == 4 and cur_dt.weekday() == 0:
            _append_opening_gap(gaps, "NWOG", i, bars, ticker.tick_size, nwog_color)
        if show_ndog and prev_dt.date() != cur_dt.date():
            _append_opening_gap(gaps, "NDOG", i, bars, ticker.tick_size, ndog_color)
    return gaps


def _append_opening_gap(gaps: list[dict[str, Any]], gtype: str, i: int, bars: list[Bar], tick_size: float, color: str) -> None:
    top = max(bars[i - 1].close, bars[i].open)
    bottom = min(bars[i - 1].close, bars[i].open)
    if top - bottom >= tick_size * 2:
        gaps.append({
            "id": f"{gtype.lower()}-{i}",
            "type": gtype,
            "top": top,
            "bottom": bottom,
            "midpoint": (top + bottom) / 2,
            "startIndex": i,
            "startTime": bars[i].ts,
            "color": color,
        })


def _killzones(bars: list[Bar], show: bool, show_ny: bool, show_ldn_open: bool, show_ldn_close: bool, show_asian: bool) -> list[dict[str, Any]]:
    if not show:
        return []
    zones: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    for i, bar in enumerate(bars):
        dt = _utc_dt(bar.ts)
        minutes = dt.hour * 60 + dt.minute
        matched = None
        color = ""
        if show_ny and 720 <= minutes <= 840:
            matched, color = "New York", "rgba(255, 93, 0, 0.12)"
        elif show_ldn_open and 420 <= minutes <= 600:
            matched, color = "London Open", "rgba(0, 188, 212, 0.12)"
        elif show_ldn_close and 900 <= minutes <= 1020:
            matched, color = "London Close", "rgba(33, 87, 243, 0.12)"
        elif show_asian and 60 <= minutes <= 300:
            matched, color = "Asian", "rgba(233, 30, 99, 0.12)"

        if matched:
            if not active or active["name"] != matched:
                if active:
                    _close_killzone(zones, active, i - 1, bars)
                active = {"name": matched, "startIdx": i, "color": color}
        elif active:
            _close_killzone(zones, active, i - 1, bars)
            active = None
    if active:
        _close_killzone(zones, active, len(bars) - 1, bars)
    return zones


def _close_killzone(zones: list[dict[str, Any]], active: dict[str, Any], end_idx: int, bars: list[Bar]) -> None:
    zones.append({
        "name": active["name"],
        "startIndex": active["startIdx"],
        "endIndex": end_idx,
        "startTime": bars[active["startIdx"]].ts,
        "endTime": bars[end_idx].ts,
        "color": active["color"],
    })
