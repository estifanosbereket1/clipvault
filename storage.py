import contextlib
import os
import sqlite3
from pathlib import Path

from content_detector import detect_type

from rapidfuzz import fuzz

FUZZY_MATCH_THRESHOLD = 60


def get_db_path():
    base_path = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    db_path = base_path + "/clipvault/history.db"
    os.makedirs(f"{base_path}/clipvault", exist_ok=True)
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
        cur.execute("PRAGMA table_info(history)")
        columns = [row["name"] for row in cur.fetchall()]
        if "pinned_at" not in columns:
            cur.execute("ALTER TABLE history ADD COLUMN pinned_at DATETIME DEFAULT NULL")
        if "content_type" not in columns:
            cur.execute("ALTER TABLE history ADD COLUMN content_type TEXT DEFAULT NULL")
        if "self_destruct" not in columns:
            cur.execute("ALTER TABLE history ADD COLUMN self_destruct BOOLEAN DEFAULT 0")
        if "origin" not in columns:
            cur.execute("ALTER TABLE history ADD COLUMN origin TEXT DEFAULT 'local'")


def get_local_entries_since(since_timestamp: str, exclude_origin: str = None):
    """
    Returns entries that:
      - originated locally on this machine (never re-broadcasts synced-in entries)
      - were created after since_timestamp
      - are not pinned or self-destruct (those never sync)
    """
    with get_connection() as conn:
        cur = conn.cursor()
        return cur.execute(
            """
            SELECT * FROM history
            WHERE origin = 'local'
              AND created_at > ?
              AND pinned = 0
              AND self_destruct = 0
            ORDER BY created_at ASC
            """,
            (since_timestamp,),
        ).fetchall()

def toggle_self_destruct(entry_id):
    with get_connection() as conn:
        cur = conn.cursor()
        current = cur.execute(
            "SELECT self_destruct FROM history WHERE id = ?", (entry_id,)
        ).fetchone()
        if current is None:
            return
        new_value = 0 if current["self_destruct"] else 1
        cur.execute(
            "UPDATE history SET self_destruct = ? WHERE id = ?", (new_value, entry_id)
        )


MAX_PINNED = 5


def get_pinned_entries():
    with get_connection() as conn:
        cur = conn.cursor()
        return cur.execute(
            "SELECT * FROM history WHERE pinned = 1 ORDER BY pinned_at DESC"
        ).fetchall()


def get_oldest_pinned_entry():
    with get_connection() as conn:
        cur = conn.cursor()
        return cur.execute(
            "SELECT * FROM history WHERE pinned = 1 ORDER BY pinned_at ASC LIMIT 1"
        ).fetchone()


def pin_entry(entry_id):
    """
    Attempts to pin an entry. Returns None on success.
    If already at MAX_PINNED, returns the oldest pinned entry instead of pinning,
    so the caller can ask the user to confirm swapping it out.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        count = cur.execute(
            "SELECT COUNT(*) as c FROM history WHERE pinned = 1"
        ).fetchone()["c"]
        if count >= MAX_PINNED:
            return get_oldest_pinned_entry()
        cur.execute(
            "UPDATE history SET pinned = 1, pinned_at = CURRENT_TIMESTAMP WHERE id = ?",
            (entry_id,),
        )
        return None


def unpin_entry(entry_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE history SET pinned = 0, pinned_at = NULL WHERE id = ?", (entry_id,)
        )


def get_recent_unpinned(limit=20):
    with get_connection() as conn:
        cur = conn.cursor()
        return cur.execute(
            "SELECT * FROM history WHERE pinned = 0 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()


def add_entry(content: str, origin: str = "local"):
    inserted = False
    content = content.strip()
    if content:
        with get_connection() as conn:
            cur = conn.cursor()
            latest_content = cur.execute(
                "SELECT content FROM history ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if latest_content is None or content != latest_content[0]:
                content_type = detect_type(content)
                cur.execute(
                    "INSERT INTO history (content, content_type, origin) VALUES (?, ?, ?)",
                    (content, content_type, origin),
                )
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

# def search_entries(query: str, limit: int = 50):
#     with get_connection() as conn:
#         cur = conn.cursor()
#         return cur.execute(
#             """
#             SELECT * FROM history
#             WHERE content LIKE ? COLLATE NOCASE
#               AND pinned = 0
#             ORDER BY created_at DESC
#             LIMIT ?
#             """,
#             (f"%{query}%", limit),
#         ).fetchall()

def search_entries(query: str, limit: int = 50):
    """
    Fuzzy-searches history for entries similar to the query, so typos and
    near-misses still match. Scores every candidate against the query and
    returns matches above FUZZY_MATCH_THRESHOLD, best matches first.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        candidates = cur.execute(
            "SELECT * FROM history WHERE pinned = 0 ORDER BY created_at DESC LIMIT 500"
        ).fetchall()

    scored = []
    for row in candidates:
        score = fuzz.partial_ratio(query.lower(), row["content"].lower())
        if score >= FUZZY_MATCH_THRESHOLD:
            scored.append((score, row))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row for score, row in scored[:limit]]
