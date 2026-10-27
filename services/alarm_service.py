from data.models import Alarm
from services.volume_baseline import (
    DEFAULT_Z_THRESHOLD,
    robust_z,
)

import logging
import math

_LOG = logging.getLogger(__name__)


def _resolve_z_threshold(params: dict) -> float:
    """Return a finite positive z-threshold, restoring the documented
    default when the persisted value is missing, non-numeric,
    non-positive, NaN or infinite (Q-42).

    A NaN/inf threshold would otherwise make the burst alarm silently
    never fire (``z >= nan`` / ``z >= inf`` is always False), so an
    invalid config must not pass through.
    """
    try:
        threshold = float(params.get("z_threshold", DEFAULT_Z_THRESHOLD))
    except (TypeError, ValueError):
        _LOG.warning("volume_burst alarm has non-numeric z_threshold %r; "
                     "restoring default %s", params.get("z_threshold"),
                     DEFAULT_Z_THRESHOLD)
        return DEFAULT_Z_THRESHOLD
    if not math.isfinite(threshold) or threshold <= 0:
        _LOG.warning("volume_burst alarm has invalid z_threshold %r; "
                     "restoring default %s", params.get("z_threshold"),
                     DEFAULT_Z_THRESHOLD)
        return DEFAULT_Z_THRESHOLD
    return threshold


def evaluate_alarms(
    prev_price: float | None,
    curr_price: float,
    alarms: list[Alarm],
) -> list[Alarm]:
    """
    Return active, untriggered alarms crossed between prev_price and curr_price.
    """
    if prev_price is None or curr_price <= 0:
        return []

    triggered: list[Alarm] = []
    for alarm in alarms:
        if alarm.kind != "price":
            continue
        if not alarm.active or alarm.triggered:
            continue

        crossed_above = prev_price < alarm.price <= curr_price
        crossed_below = prev_price > alarm.price >= curr_price

        if alarm.direction == "cross_above" and crossed_above:
            triggered.append(alarm)
        elif alarm.direction == "cross_below" and crossed_below:
            triggered.append(alarm)
        elif alarm.direction == "cross_either" and (crossed_above or crossed_below):
            triggered.append(alarm)

    return triggered


def evaluate_volume_burst(
    volume_per_min: float,
    baseline: tuple[float, float, int, str] | None,
    alarms: list[Alarm],
) -> list[Alarm]:
    """D39.3: evaluate ``volume_burst`` alarms against a robust baseline.

    ``baseline`` is ``(median, mad, n, source)`` from
    :meth:`VolumeBaselineService.baseline` (per-minute units), or ``None``
    while warming up — in which case nothing fires. An alarm fires when
    the robust z-score of the bar's per-minute volume is at or above its
    user-tunable ``params["z_threshold"]`` (default
    ``DEFAULT_Z_THRESHOLD``). Z-score semantics throughout — no K-multiple
    language (C39.1).

    Each fired alarm gets its transient ``trigger_z`` set (fire-time
    z-score for the toast; never persisted). Price alarms are ignored here
    (``evaluate_alarms`` owns them).
    """
    if baseline is None:
        return []
    med, mad_value, _n, _source = baseline
    triggered: list[Alarm] = []
    for alarm in alarms:
        if alarm.kind != "volume_burst":
            continue
        if not alarm.active or alarm.triggered:
            continue
        try:
            threshold = _resolve_z_threshold(alarm.params)
        except (TypeError, ValueError, AttributeError):
            threshold = DEFAULT_Z_THRESHOLD
        z = robust_z(volume_per_min, med, mad_value)
        if z >= threshold:
            alarm.trigger_z = z
            triggered.append(alarm)
    return triggered
