import sqlite3
from contextlib import contextmanager
from .config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                bike_id     TEXT NOT NULL,
                serial      TEXT NOT NULL,
                length_min  INTEGER NOT NULL,
                start_time  TEXT NOT NULL,
                end_time    TEXT NOT NULL,
                start_pos   TEXT NOT NULL,
                end_pos     TEXT NOT NULL,
                image_url   TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
