"""
drawing_service.py
Pure data logic for the drawing tools: kind validation, group naming,
payload normalization, Fibonacci level math, and drawing summaries.

No Qt imports here — keep it unit-testable in isolation.
"""

from typing import Optional

from data.models import Drawing, DrawingGroup

DRAWING_KINDS = ("trendline", "horizontal", "zone", "fibonacci", "measure")

FIB_LEVELS = (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0)
FIB_EXTENSION_LEVELS = (0.0, 0.618, 1.0, 1.272, 1.618, 2.0, 2.618)

DEFAULT_DRAWING_COLOR = "#38bdf8"


def auto_group_name(seq_number: int) -> str:
    """Reference-style automatic group name."""
    return f"DrawingSet_{seq_number}"


def next_group_seq(groups: list[DrawingGroup]) -> int:
    """Next sequence number for a symbol's drawing groups."""
    return max((g.seq_number for g in groups), default=0) + 1


def _point(value) -> dict:
    if isinstance(value, dict):
        try:
            x = int(value.get("x"))
            y = float(value.get("y"))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid point: {value!r}")
        return {"x": x, "y": y}
    raise ValueError(f"Point must be a dict, got {value!r}")


def normalize_payload(kind: str, payload: dict) -> dict:
    """Validate and sanitize a drawing payload for the given kind.

    Raises ValueError on malformed input; guarantees stable keys.
    """
    if kind not in DRAWING_KINDS:
        raise ValueError(f"Unknown drawing kind: {kind!r}")
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dict")

    if kind in ("trendline", "measure"):
        return {"p1": _point(payload.get("p1")), "p2": _point(payload.get("p2"))}

    if kind == "horizontal":
        try:
            return {"y": float(payload["y"])}
        except (KeyError, TypeError, ValueError):
            raise ValueError("Horizontal requires numeric 'y'")

    if kind == "zone":
        try:
            x1, x2 = int(payload["x1"]), int(payload["x2"])
            y1, y2 = float(payload["y1"]), float(payload["y2"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("Zone requires x1/x2 (int) and y1/y2 (float)")
        if y1 > y2:
            y1, y2 = y2, y1
        if x1 > x2:
            x1, x2 = x2, x1
        return {"x1": x1, "x2": x2, "y1": y1, "y2": y2}

    if kind == "fibonacci":
        fib_type = payload.get("type", "retr")
        if fib_type not in ("retr", "ext"):
            raise ValueError(f"Fib type must be 'retr' or 'ext', got {fib_type!r}")
        return {
            "p1": _point(payload.get("p1")),
            "p2": _point(payload.get("p2")),
            "type": fib_type,
        }

    raise ValueError(f"Unhandled kind: {kind!r}")


def fib_levels(y1: float, y2: float, fib_type: str = "retr") -> list[tuple[float, float]]:
    """Return [(ratio, price)] for the reference Fibonacci levels."""
    ratios = FIB_EXTENSION_LEVELS if fib_type == "ext" else FIB_LEVELS
    return [(ratio, y1 + ratio * (y2 - y1)) for ratio in ratios]


def points_in_ts(kind: str, payload: dict) -> list[tuple[int, float]]:
    """Anchor points as [(timestamp, price)] for hit-testing and handles."""
    p = normalize_payload(kind, payload)
    if kind in ("trendline", "measure", "fibonacci"):
        return [(p["p1"]["x"], p["p1"]["y"]), (p["p2"]["x"], p["p2"]["y"])]
    if kind == "horizontal":
        return [(0, p["y"])]
    if kind == "zone":
        return [(p["x1"], p["y1"]), (p["x1"], p["y2"])]
    raise ValueError(f"Unhandled kind: {kind!r}")


def drawing_summary(drawing: Drawing) -> str:
    """Human-readable label for dialogs / lists."""
    try:
        p = normalize_payload(drawing.kind, drawing.payload)
    except ValueError:
        return drawing.kind.title()
    if drawing.kind in ("trendline", "measure"):
        return "Trendline" if drawing.kind == "trendline" else "Measure"
    if drawing.kind == "horizontal":
        return f"H @ {p['y']:.2f}"
    if drawing.kind == "zone":
        return f"Zone {p['y1']:.2f}–{p['y2']:.2f}"
    if drawing.kind == "fibonacci":
        return f"Fib {p['type'].upper()}"
    return drawing.kind.title()