"""
indicator_service.py
Pure numeric math — no Qt, no IBKR, no I/O.
All functions accept List[float] and return List[float | None].
None is used for periods where the indicator is not yet valid.
"""

from datetime import datetime
from typing import List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback
    from backports.zoneinfo import ZoneInfo  # type: ignore

_EASTERN = ZoneInfo("America/New_York")
import math


def _ensure(prices: List[float], period: int) -> bool:
    return len(prices) >= period


# ── Simple Moving Average ──────────────────────────────────────────────────────

def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = [None] * len(prices)
    for i in range(period - 1, len(prices)):
        result[i] = sum(prices[i - period + 1 : i + 1]) / period
    return result


# ── Exponential Moving Average ─────────────────────────────────────────────────

def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = [None] * len(prices)
    if not _ensure(prices, period):
        return result
    k = 2 / (period + 1)
    # Seed with SMA of first `period` bars
    seed = sum(prices[:period]) / period
    result[period - 1] = seed
    for i in range(period, len(prices)):
        result[i] = prices[i] * k + result[i - 1] * (1 - k)
    return result


# ── VWAP (session-scoped, resets at each session/day boundary) ─────────────────

def calculate_vwap(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    timestamps: Optional[List[int]] = None,
) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    cum_tpv = 0.0
    cum_vol = 0.0
    if timestamps is None:
        for h, l, c, v in zip(highs, lows, closes, volumes):
            tp = (h + l + c) / 3
            cum_tpv += tp * v
            cum_vol += v
            result.append(cum_tpv / cum_vol if cum_vol > 0 else None)
        return result

    prev_day = None
    for h, l, c, v, ts in zip(highs, lows, closes, volumes, timestamps):
        # D27.8: session-anchored VWAP resets on the ET date change, not the
        # UTC day boundary (which sits mid-session for US equities).
        day = datetime.fromtimestamp(ts, tz=_EASTERN).date()
        if prev_day is None:
            cum_tpv = 0.0
            cum_vol = 0.0
            prev_day = day
        elif day != prev_day:
            cum_tpv = 0.0
            cum_vol = 0.0
            prev_day = day
        tp = (h + l + c) / 3
        cum_tpv += tp * v
        cum_vol += v
        result.append(cum_tpv / cum_vol if cum_vol > 0 else None)
    return result


# ── Bollinger Bands ────────────────────────────────────────────────────────────

def calculate_bollinger_bands(
    prices: List[float], period: int = 20, std_dev: float = 2.0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Returns (upper, middle, lower)."""
    middle = calculate_sma(prices, period)
    upper: List[Optional[float]] = [None] * len(prices)
    lower: List[Optional[float]] = [None] * len(prices)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        avg = middle[i]
        if avg is None:
            continue
        variance = sum((x - avg) ** 2 for x in window) / period
        sd = math.sqrt(variance)
        upper[i] = avg + std_dev * sd
        lower[i] = avg - std_dev * sd
    return upper, middle, lower


# ── RSI ───────────────────────────────────────────────────────────────────────

def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    result: List[Optional[float]] = [None] * len(prices)
    if len(prices) < period + 1:
        return result
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(prices)):
        idx = i - 1  # delta index
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - (100 / (1 + rs))
    return result


# ── MACD ──────────────────────────────────────────────────────────────────────

def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line: List[Optional[float]] = []
    for f, s in zip(ema_fast, ema_slow):
        macd_line.append(f - s if f is not None and s is not None else None)

    # Signal = EMA of MACD line (skip leading Nones)
    valid_start = next((i for i, v in enumerate(macd_line) if v is not None), None)
    signal_line: List[Optional[float]] = [None] * len(macd_line)
    histogram: List[Optional[float]] = [None] * len(macd_line)
    if valid_start is not None:
        valid_values = [v for v in macd_line if v is not None]
        sig_values = calculate_ema(valid_values, signal_period)
        j = 0
        for i in range(valid_start, len(macd_line)):
            if j < len(sig_values):
                signal_line[i] = sig_values[j]
                if macd_line[i] is not None and sig_values[j] is not None:
                    histogram[i] = macd_line[i] - sig_values[j]
                j += 1
    return macd_line, signal_line, histogram
