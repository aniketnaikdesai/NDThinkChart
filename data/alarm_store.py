import time

from data.db import db
from data.models import Alarm


class AlarmStore:
    """Main-thread SQLite access for price alarms."""

    @staticmethod
    def load(symbol: str) -> list[Alarm]:
        cursor = db.conn.cursor()
        cursor.execute(
            """
            SELECT id, symbol, price, direction, active, triggered, triggered_at,
                   sound, note, created_at
            FROM alarms
            WHERE symbol=?
            ORDER BY price DESC
            """,
            (symbol,),
        )
        return [AlarmStore._from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def add(alarm: Alarm) -> int:
        created_at = alarm.created_at or int(time.time())
        cursor = db.conn.cursor()
        cursor.execute(
            """
            INSERT INTO alarms (
                symbol, price, direction, active, triggered, triggered_at,
                sound, note, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alarm.symbol,
                alarm.price,
                alarm.direction,
                1 if alarm.active else 0,
                1 if alarm.triggered else 0,
                alarm.triggered_at,
                1 if alarm.sound else 0,
                alarm.note,
                created_at,
            ),
        )
        db.conn.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def mark_triggered(alarm_id: int, triggered_at: int | None = None) -> None:
        db.conn.execute(
            "UPDATE alarms SET triggered=1, triggered_at=? WHERE id=?",
            (triggered_at or int(time.time()), alarm_id),
        )
        db.conn.commit()

    _EDITABLE = {"price", "direction", "active", "triggered", "triggered_at",
                 "sound", "note"}

    @staticmethod
    def update(alarm_id: int, **fields) -> None:
        columns = [key for key in fields if key in AlarmStore._EDITABLE]
        if not columns:
            return
        assignments = ", ".join(f"{name}=?" for name in columns)
        values = []
        for name in columns:
            value = fields[name]
            if name in ("active", "triggered", "sound"):
                value = 1 if value else 0
            values.append(value)
        values.append(alarm_id)
        db.conn.execute(
            f"UPDATE alarms SET {assignments} WHERE id=?", values
        )
        db.conn.commit()

    @staticmethod
    def set_price(alarm_id: int, price: float) -> None:
        AlarmStore.update(alarm_id, price=float(price))

    @staticmethod
    def set_sound(alarm_id: int, sound: bool) -> None:
        AlarmStore.update(alarm_id, sound=bool(sound))

    @staticmethod
    def rearm(alarm_id: int) -> None:
        db.conn.execute(
            "UPDATE alarms SET triggered=0, triggered_at=NULL, active=1 WHERE id=?",
            (alarm_id,),
        )
        db.conn.commit()

    @staticmethod
    def delete(alarm_id: int) -> None:
        db.conn.execute("DELETE FROM alarms WHERE id=?", (alarm_id,))
        db.conn.commit()

    @staticmethod
    def _from_row(row) -> Alarm:
        return Alarm(
            id=row[0],
            symbol=row[1],
            price=row[2],
            direction=row[3],
            active=bool(row[4]),
            triggered=bool(row[5]),
            triggered_at=row[6],
            sound=bool(row[7]),
            note=row[8] or "",
            created_at=row[9],
        )
