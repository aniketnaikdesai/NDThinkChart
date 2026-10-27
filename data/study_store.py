import json
import math
from copy import deepcopy
from typing import Iterable

from data.db import db

#: Documented per-study defaults for the numeric params the indicator
#: math consumes (mirrors ``ui/studies_dialog.DEFAULT_STUDIES``). Used
#: to restore a sane value when a persisted param is invalid (Q-42).
_DEFAULT_STUDY_PARAMS: dict[str, dict] = {
    "sma": {"period": 20},
    "ema": {"period": 9},
    "ema2": {"period": 21},
    "bollinger": {"period": 20, "std_dev": 2.0},
    "rsi": {"period": 14},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
}

_PERIOD_KEYS = ("period", "fast", "slow", "signal")


def _is_valid_period(value) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value > 0
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return value > 0
    return False


def sanitize_study_params(study_type: str, params: dict) -> dict:
    """Return ``params`` with invalid numeric study params restored to
    their documented defaults (Q-42).

    Unknown study types and non-numeric keys pass through untouched.
    ``period``/``fast``/``slow``/``signal`` must be positive ints
    (integral floats are coerced); ``std_dev`` must be finite and
    non-negative. Anything else (zero, negative, NaN, inf, bools,
    strings) is replaced with the default for that study type.
    """
    defaults = _DEFAULT_STUDY_PARAMS.get(study_type)
    if not defaults or not isinstance(params, dict):
        return params
    cleaned = dict(params)
    for key in _PERIOD_KEYS:
        if key in defaults and key in cleaned:
            if _is_valid_period(cleaned[key]):
                v = cleaned[key]
                cleaned[key] = int(v) if isinstance(v, float) else v
            else:
                cleaned[key] = defaults[key]
    if "std_dev" in defaults and "std_dev" in cleaned:
        v = cleaned["std_dev"]
        if isinstance(v, bool):
            cleaned["std_dev"] = defaults["std_dev"]
        else:
            try:
                fv = float(v)
            except (TypeError, ValueError):
                cleaned["std_dev"] = defaults["std_dev"]
            else:
                if not math.isfinite(fv) or fv < 0:
                    cleaned["std_dev"] = defaults["std_dev"]
                else:
                    cleaned["std_dev"] = fv
    return cleaned


class StudyStore:
    """SQLite persistence for per-symbol study configuration."""

    @staticmethod
    def load(symbol: str) -> list[dict]:
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT type, enabled, params FROM studies WHERE symbol=? ORDER BY id ASC",
            (symbol,),
        )
        studies: list[dict] = []
        for study_type, enabled, params_json in cursor.fetchall():
            try:
                params = json.loads(params_json)
            except (TypeError, json.JSONDecodeError):
                params = {}
            if not isinstance(params, dict):
                params = {}
            studies.append({
                "type": study_type,
                "enabled": bool(enabled),
                "params": sanitize_study_params(study_type, params),
            })
        return studies

    @staticmethod
    def save(symbol: str, studies: Iterable[dict]) -> None:
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM studies WHERE symbol=?", (symbol,))
        cursor.executemany(
            """
            INSERT INTO studies (symbol, type, enabled, params)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    symbol,
                    study["type"],
                    1 if study.get("enabled") else 0,
                    json.dumps(deepcopy(study.get("params", {}))),
                )
                for study in studies
            ],
        )
        db.conn.commit()
