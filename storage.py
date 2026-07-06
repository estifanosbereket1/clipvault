import contextlib
import os
import sqlite3
from pathlib import Path


def get_db_path():
    base_path = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    db_path = base_path + "/clipqr/history.db"
    os.makedirs(f"{base_path}/clipqr", exist_ok=True)
    return Path(db_path)


@contextlib.contextmanager
def get_connection():
    # setup
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        # teardown
        conn.commit()
        conn.close()


def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY,content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, pinned BOOLEAN DEFAULT 0)"
        )


def add_entry(content: str):
    inserted = False
    content = content.strip()
    if content:
        with get_connection() as conn:
            cur = conn.cursor()
            latest_content = cur.execute(
                "SELECT content FROM history ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if latest_content is None or content != latest_content[0]:
                cur.execute("INSERT INTO history (content) VALUES (?)", (content,))
                inserted = True
    return inserted


def get_history(limit=20):
    with get_connection() as conn:
        cur = conn.cursor()
        latest_contents = cur.execute(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT (?)", (limit,)
        ).fetchall()
        return latest_contents


def get_entry_by_id(entry_id):
    with get_connection() as conn:
        cur = conn.cursor()
        entry = cur.execute(
            "SELECT * FROM history WHERE id = (?)", (entry_id,)
        ).fetchone()
        return entry


def delete_entry(entry_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM history where id = (?)", (entry_id,))
        rows_deleted = cur.rowcount
        return rows_deleted


def clear_history():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM history")
