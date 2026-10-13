"""Volume baseline service for D39 unusual-volume burst alerts.

Robust z-score baseline (median/MAD — never mean/stddev) per
``(resolved contract, time-of-day bucket)`` over at most ``N_BASELINE_BARS``
(30) samples, per the owner decisions of 2026-10-13.

Three-tier source chain (plan §5 item 39.2):

1. **Persisted baseline table** — ``volume_baseline(resolved_contract,
   bucket, median, mad, n, samples, updated_at)``; the steady state after
   days of use. Rows are keyed on the *resolved* contract (e.g. ``ESZ6``,
   never bare ``ES`` — the D36 ``footprint_cache_key`` rule, C39.2), so a
   contract roll can never compare ESZ5 volume against an ESU5 baseline:
   the new contract simply has no rows yet.
2. **One-time prime from ``BarCache``** — when a session starts with
   multi-day history cached locally, the cached bars are bucketed once and
   persisted. Local read only — no IBKR requests, no pacing impact.
3. **Rolling last-30-bars fallback** — until a bucket fills, the baseline
   falls back to the last 30 bars' per-minute volumes regardless of
   time-of-day (documented approximation, not same-time-of-day).

Guards (binding):

- **Volume floor** — buckets whose median per-minute volume is below
  ``VOLUME_FLOOR_PER_MIN`` are too thin to evaluate (no divide-by-noise
  triggers on illiquid names).
- **Warm-up** — no evaluation until ``MIN_WARMUP_BARS`` samples exist for
  the bucket (or the rolling fallback). The open-coverage gap this creates
  early in a session is documented, not silent: :meth:`status` reports it.
- **MAD floor** — a flat (zero-variance) baseline gets a MAD floor of 5%
  of the median so a genuine burst still produces a finite, large z while
  flat data scores ~0 and never fires.

Bar volumes are normalized per-minute (``TIMEFRAME_SECONDS / 60``) so mixed
timeframes compare; "1 day" bars use 390 regular-session minutes.
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

from data.bar_aggregator import TIMEFRAME_SECONDS

_LOG = logging.getLogger(__name__)

_EASTERN = ZoneInfo("America/New_York")

#: Baseline window — owner decision N = 30 bars.
N_BASELINE_BARS = 30
#: Minimum samples before any evaluation (the documented open-coverage gap).
MIN_WARMUP_BARS = 5
#: Buckets thinner than this per-minute volume are not evaluated.
VOLUME_FLOOR_PER_MIN = 1.0
#: MAD floor as a fraction of the median (flat-baseline guard).
MAD_FLOOR_RATIO = 0.05
#: Default user-tunable z-score threshold for a burst.
DEFAULT_Z_THRESHOLD = 4.0
#: Regular-session minutes used to normalize "1 day" bars.
DAY_SESSION_MINUTES = 390.0


# ── Pure statistics ──────────────────────────────────────────────────────

def median(xs: list[float]) -> float:
    """Median of a non-empty sample list."""
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def mad(xs: list[float], med: float | None = None) -> float:
    """Median absolute deviation of a non-empty sample list."""
    if med is None:
        med = median(xs)
    return median([abs(x - med) for x in xs])


def robust_z(x: float, med: float, mad_value: float) -> float:
    """Robust z-score: ``0.6745 * (x - median) / MAD``.

    The 0.6745 factor makes MAD consistent with the standard deviation for
    normal data. ``mad_value`` is floored at ``MAD_FLOOR_RATIO`` of the
    median so a flat baseline yields a finite (large) z for real bursts
    while flat data scores ~0.
    """
    mad_eff = max(mad_value, MAD_FLOOR_RATIO * med, 1e-9)
    return 0.6745 * (x - med) / mad_eff


# ── Bucketing / normalization ────────────────────────────────────────────

def bucket_for_ts(ts: int) -> int:
    """Minute-of-day bucket (0–1439) in America/New_York for a bar timestamp."""
    dt = datetime.fromtimestamp(ts, tz=_EASTERN)
    return dt.hour * 60 + dt.minute


def minutes_for_timeframe(timeframe: str) -> float:
    """Bar period in minutes, for per-minute volume normalization."""
    if timeframe == "1 day":
        return DAY_SESSION_MINUTES
    secs = TIMEFRAME_SECONDS.get(timeframe)
    if not secs:
        return 1.0
    return secs / 60.0


# ── Service ──────────────────────────────────────────────────────────────

class VolumeBaselineService:
    """Per-(resolved-contract, time-of-day-bucket) robust volume baselines.

    The service is meant to be shared (one per application, owned by the
    main window): sessions for different symbols share nothing because the
    key already contains the resolved contract, while two sessions on the
    same tape (e.g. an ES chart and an SPX proxy monitor) share one
    baseline — which is exactly right.
    """

    def __init__(self):
        # (resolved_key, bucket) -> deque[float] of per-minute volumes,
        # newest last, capped at N_BASELINE_BARS. Seeded from the DB on
        # first use per key; appended by record().
        self._samples: dict[tuple[str, int], deque[float]] = {}
        # resolved_key -> deque[float] of the last <=30 per-minute volumes
        # across all buckets (tier-3 rolling fallback).
        self._rolling: dict[str, deque[float]] = {}
        # resolved keys already primed from BarCache (one-time per key).
        self._primed: set[str] = set()
        # resolved keys whose DB rows have been loaded into _samples.
        self._loaded: set[str] = set()
        # resolved keys explicitly invalidated (roll): DB rows for them are
        # never resurrected into memory — the key starts empty.
        self._tombstoned: set[str] = set()

    # ── Recording ────────────────────────────────────────────────────

    def record(
        self,
        resolved_key: str,
        ts: int,
        timeframe: str,
        volume: float,
    ) -> None:
        """Record one *completed* bar into the baseline (never a forming bar).

        Only completed bars are recorded — the caller tracks forming bars
        and calls this when a bar completes, so partial bars never pollute
        the baseline.
        """
        if resolved_key in self._tombstoned:
            return  # invalidated (roll): a stale key can never be re-persisted
        per_min = volume / minutes_for_timeframe(timeframe)
        bucket = bucket_for_ts(ts)
        self._ensure_loaded(resolved_key)
        key = (resolved_key, bucket)
        dq = self._samples.setdefault(key, deque(maxlen=N_BASELINE_BARS))
        dq.append(per_min)
        rolling = self._rolling.setdefault(
            resolved_key, deque(maxlen=N_BASELINE_BARS))
        rolling.append(per_min)
        self._persist_bucket(resolved_key, bucket, dq)

    # ── Evaluation ───────────────────────────────────────────────────

    def baseline(
        self, resolved_key: str, ts: int
    ) -> tuple[float, float, int, str] | None:
        """Return ``(median, mad, n, source)`` for the bar at ``ts``.

        Source is ``"tod"`` (same-time-of-day bucket) or ``"rolling"``
        (tier-3 fallback). ``None`` means no evaluation is possible yet —
        the caller must skip the alarm check (warm-up gap, documented).
        """
        self._ensure_loaded(resolved_key)
        bucket = bucket_for_ts(ts)
        dq = self._samples.get((resolved_key, bucket), deque())
        if len(dq) >= MIN_WARMUP_BARS:
            med = median(list(dq))
            if med < VOLUME_FLOOR_PER_MIN:
                return None
            return med, mad(list(dq), med), len(dq), "tod"
        rolling = self._rolling.get(resolved_key, deque())
        if len(rolling) >= MIN_WARMUP_BARS:
            med = median(list(rolling))
            if med < VOLUME_FLOOR_PER_MIN:
                return None
            return med, mad(list(rolling), med), len(rolling), "rolling"
        return None

    def status(self, resolved_key: str, ts: int) -> str:
        """Human-readable readiness for the UI ("warming up (3/5)" etc.)."""
        self._ensure_loaded(resolved_key)
        bucket = bucket_for_ts(ts)
        n = len(self._samples.get((resolved_key, bucket), ()))
        if n >= MIN_WARMUP_BARS:
            return "ready"
        n_roll = len(self._rolling.get(resolved_key, ()))
        have = max(n, n_roll)
        return f"warming up ({have}/{MIN_WARMUP_BARS})"

    def evaluate(
        self,
        resolved_key: str,
        ts: int,
        volume_per_min: float,
        z_threshold: float = DEFAULT_Z_THRESHOLD,
    ) -> tuple[bool, float | None]:
        """Evaluate one bar's per-minute volume.

        Returns ``(fired, z)`` — ``fired`` is True when the robust z-score
        is at or above ``z_threshold``. ``z`` is None when no baseline
        exists yet (warm-up).
        """
        base = self.baseline(resolved_key, ts)
        if base is None:
            return False, None
        med, mad_value, _n, _source = base
        z = robust_z(volume_per_min, med, mad_value)
        return z >= z_threshold, z

    # ── Priming / invalidation ───────────────────────────────────────

    def is_primed(self, resolved_key: str) -> bool:
        """True once this key has been primed from BarCache (one-time)."""
        return resolved_key in self._primed

    def prime_from_bars(
        self,
        resolved_key: str,
        bars: list,
    ) -> int:
        """One-time prime of same-time-of-day buckets from cached bars.

        ``bars`` are completed historical bars (e.g. from
        ``BarCache.get_bars``) with ``.ts``, ``.timeframe`` and ``.volume``.
        Newest-30 samples per bucket are kept. Returns the number of bars
        consumed. Local read only — no IBKR requests.
        """
        if resolved_key in self._primed:
            return 0
        self._primed.add(resolved_key)
        self._ensure_loaded(resolved_key)
        touched: set[int] = set()
        # Oldest-first so the newest 30 survive the cap.
        for bar in bars:
            tf = getattr(bar, "timeframe", "1 min")
            per_min = bar.volume / minutes_for_timeframe(tf)
            bucket = bucket_for_ts(bar.ts)
            key = (resolved_key, bucket)
            dq = self._samples.setdefault(key, deque(maxlen=N_BASELINE_BARS))
            dq.append(per_min)
            touched.add(bucket)
        for bucket in touched:
            self._persist_bucket(
                resolved_key, bucket, self._samples[(resolved_key, bucket)])
        _LOG.info("VolumeBaseline: primed %s from %d cached bars (%d buckets)",
                  resolved_key, len(bars), len(touched))
        return len(bars)

    def invalidate(self, resolved_key: str) -> None:
        """Drop all state for a resolved contract (roll handling).

        In-memory deques are dropped AND the key is tombstoned so a later
        DB load cannot resurrect the old contract's samples. The new
        front-month key simply starts with no rows — never comparing one
        contract's volume against another's baseline (C39.2).
        """
        for key in [k for k in self._samples if k[0] == resolved_key]:
            del self._samples[key]
        self._rolling.pop(resolved_key, None)
        self._primed.discard(resolved_key)
        self._loaded.discard(resolved_key)
        self._tombstoned.add(resolved_key)

    # ── Persistence ──────────────────────────────────────────────────

    def _ensure_loaded(self, resolved_key: str) -> None:
        if resolved_key in self._loaded:
            return
        self._loaded.add(resolved_key)
        if resolved_key in self._tombstoned:
            return  # invalidated (roll): start empty, never resurrect
        from data.db import db
        cur = db.conn.cursor()
        cur.execute(
            "SELECT bucket, samples FROM volume_baseline "
            "WHERE resolved_contract=?",
            (resolved_key,),
        )
        for bucket, samples_json in cur.fetchall():
            try:
                samples = json.loads(samples_json or "[]")
            except (ValueError, TypeError):
                samples = []
            dq: deque[float] = deque(maxlen=N_BASELINE_BARS)
            for v in samples[-N_BASELINE_BARS:]:
                dq.append(float(v))
                self._rolling.setdefault(
                    resolved_key, deque(maxlen=N_BASELINE_BARS)).append(float(v))
            self._samples[(resolved_key, int(bucket))] = dq

    def _persist_bucket(
        self, resolved_key: str, bucket: int, dq: deque[float]
    ) -> None:
        samples = list(dq)
        if not samples:
            return
        med = median(samples)
        mad_value = mad(samples, med)
        from data.db import db
        db.conn.execute(
            """
            INSERT INTO volume_baseline
                (resolved_contract, bucket, median, mad, n, samples, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(resolved_contract, bucket) DO UPDATE SET
                median=excluded.median, mad=excluded.mad, n=excluded.n,
                samples=excluded.samples, updated_at=excluded.updated_at
            """,
            (resolved_key, bucket, med, mad_value, len(samples),
             json.dumps(samples), int(time.time())),
        )
        db.conn.commit()
