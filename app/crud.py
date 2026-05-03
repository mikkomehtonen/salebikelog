"""Database CRUD operations with typed return values."""

from typing import Any, cast

from .database import get_db
from .schemas.trip import TripCreate

Row = dict[str, Any]


def create_trip(data: TripCreate, image_url: str) -> int:
    """Insert a trip and return its ID."""
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
        if trip_id is None:
            msg = "Failed to create trip: no row ID returned"
            raise RuntimeError(msg)
        return trip_id


def get_trip(trip_id: int) -> Row | None:
    """Fetch a trip by ID, returning dict or None."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
        return dict(row) if row else None


def list_trips(limit: int = 50, offset: int = 0) -> list[Row]:
    """List trips ordered by created_at descending."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM trips ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_trip(trip_id: int) -> bool:
    """Delete a trip by ID. Returns True if a row was removed."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
        conn.commit()
        return cursor.rowcount > 0


def create_position(
    name: str,
    latitude: float | None,
    longitude: float | None,
    altitude: float | None,
) -> int:
    """Insert a position, returning its ID (idempotent by name)."""
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO positions (name, latitude, longitude, altitude)
                VALUES (?, ?, ?, ?)
                """,
                (name, latitude, longitude, altitude),
            )
            conn.commit()
        except conn.IntegrityError:
            row = conn.execute(
                "SELECT id FROM positions WHERE name = ?",
                (name,),
            ).fetchone()
            if row:
                row_id = row["id"]
                if row_id is not None:
                    return cast("int", row_id)
            msg = f"Failed to find or create position: {name}"
            raise RuntimeError(msg) from None
        else:
            lastrowid = cursor.lastrowid
            if lastrowid is not None:
                return lastrowid
            msg = "Failed to create position: no row ID returned"
            raise RuntimeError(msg)


def get_position_by_name(name: str) -> Row | None:
    """Fetch a position by name, returning dict or None."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM positions WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None


def get_position_by_id(position_id: int) -> Row | None:
    """Fetch a position by ID, returning dict or None."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM positions WHERE id = ?",
            (position_id,),
        ).fetchone()
        return dict(row) if row else None


def update_position(
    position_id: int,
    latitude: float | None,
    longitude: float | None,
    altitude: float | None,
) -> bool:
    """Update position coordinates. Returns True if a row was updated."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            UPDATE positions SET latitude = ?, longitude = ?, altitude = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (latitude, longitude, altitude, position_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_positions(limit: int = 50, offset: int = 0) -> list[Row]:
    """List positions ordered by name ascending."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM positions ORDER BY name ASC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_position(position_id: int) -> bool:
    """Delete a position by ID. Returns True if a row was removed."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM positions WHERE id = ?", (position_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_unmatched_positions() -> list[dict[str, object]]:
    """Return trip positions that have no entry in the positions table."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT t.start_pos as name, 'start_pos' as source, t.id as trip_id
            FROM trips t
            WHERE t.start_pos NOT IN (SELECT name FROM positions)
            UNION ALL
            SELECT t.end_pos, 'end_pos', t.id
            FROM trips t
            WHERE t.end_pos NOT IN (SELECT name FROM positions)
            """,
        ).fetchall()
        return [dict(r) for r in rows]
