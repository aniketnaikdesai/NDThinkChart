import json
from copy import deepcopy
from typing import Iterable

from data.db import db


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
            studies.append({
                "type": study_type,
                "enabled": bool(enabled),
                "params": params,
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
