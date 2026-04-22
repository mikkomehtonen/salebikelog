from .database import get_db
from .schemas.trip import TripCreate


def create_trip(data: TripCreate, image_url: str):
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO trips (bike_id, serial, length_min, start_time, end_time, start_pos, end_pos, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.bike_id,
                data.serial,
                data.length_min,
                data.start_time.isoformat(),
                data.end_time.isoformat(),
                data.start_pos,
                data.end_pos,
                image_url,
            ),
        )
        conn.commit()
        trip_id = cursor.lastrowid
        return trip_id


def get_trip(trip_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        return dict(row) if row else None


def list_trips(limit: int = 50, offset: int = 0):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM trips ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_trip(trip_id: int):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
        return cursor.rowcount > 0
