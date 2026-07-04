import os
import sqlite3
from pathlib import Path


def get_db_path():
    base_path = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    db_path = base_path + "/clipqr/history.db"
    os.makedirs(f"{base_path}/clipqr", exist_ok=True)
    return Path(db_path)


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY,content TEXT NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, pinned BOOLEAN DEFAULT 0)"
    )
    conn.commit()
    conn.close()


def add_entry(content: str):
    inserted = False
    content = content.strip()
    if content:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        latest_content = cur.execute(
            "SELECT content FROM history ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if latest_content is None or content != latest_content[0]:
            cur.execute("INSERT INTO history (content) values (?)", (content,))
            print(f"{content} insterted")
            inserted = True

        conn.commit()
        conn.close()
    return inserted


def get_history(limit=20):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    latest_contents = cur.execute(
        "SELECT * FROM history ORDER BY created_at DESC LIMIT (?)", (limit,)
    ).fetchall()
    conn.close()
    return latest_contents
