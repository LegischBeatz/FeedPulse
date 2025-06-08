import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).resolve().parent / "articles.db"

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                date TEXT,
                hash TEXT UNIQUE
            )
            """
        )
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rewritten_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                content TEXT,
                date TEXT,
                category TEXT,
                hash TEXT UNIQUE
            )
            """
        )
        # Add category column if the database was created without it
        cur = _conn.execute("PRAGMA table_info(rewritten_articles)")
        cols = [r[1] for r in cur.fetchall()]
        if "category" not in cols:
            _conn.execute("ALTER TABLE rewritten_articles ADD COLUMN category TEXT")
            _conn.commit()
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_status (
                url TEXT PRIMARY KEY,
                checked_at TEXT,
                success INTEGER,
                reason TEXT
            )
            """
        )
        _conn.commit()
    return _conn

def compute_hash(title: str, date: str) -> str:
    return hashlib.sha256(f"{title}{date}".encode("utf-8")).hexdigest()

def store_processed_article(title: str, link: str, date: str) -> bool:
    conn = get_conn()
    h = compute_hash(title, date)
    try:
        conn.execute(
            "INSERT INTO processed_articles (title, link, date, hash) VALUES (?, ?, ?, ?)",
            (title, link, date, h),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def store_rewritten_article(
    title: str, link: str, content: str, date: str, category: Optional[str] = None
) -> bool:
    conn = get_conn()
    h = compute_hash(title, date)
    try:
        conn.execute(
            "INSERT INTO rewritten_articles (title, link, content, date, category, hash) VALUES (?, ?, ?, ?, ?, ?)",
            (title, link, content, date, category, h),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_rewritten_article(article_hash: str) -> Optional[Dict[str, str]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT title, link, content, date FROM rewritten_articles WHERE hash = ?",
        (article_hash,),
    )
    row = cur.fetchone()
    if row:
        return {"title": row[0], "link": row[1], "content": row[2], "date": row[3]}
    return None


def list_rewritten_articles() -> List[Dict[str, str]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT id, title, link, content, date, category FROM rewritten_articles ORDER BY id DESC"
    )
    rows = cur.fetchall()
    return [
        {
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "content": row[3],
            "date": row[4],
            "category": row[5],
        }
        for row in rows
    ]


def delete_article(article_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute(
        "DELETE FROM rewritten_articles WHERE id = ?",
        (article_id,),
    )
    conn.commit()
    return cur.rowcount > 0


def update_article_category(article_id: int, category: str) -> bool:
    conn = get_conn()
    cur = conn.execute(
        "UPDATE rewritten_articles SET category = ? WHERE id = ?",
        (category, article_id),
    )
    conn.commit()
    return cur.rowcount > 0


def record_feed_status(url: str, success: bool, reason: str) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO feed_status (url, checked_at, success, reason)
        VALUES (?, datetime('now'), ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            checked_at = excluded.checked_at,
            success = excluded.success,
            reason = excluded.reason
        """,
        (url, int(success), reason),
    )
    conn.commit()


def get_failed_feeds() -> List[str]:
    conn = get_conn()
    cur = conn.execute("SELECT url FROM feed_status WHERE success = 0")
    return [row[0] for row in cur.fetchall()]
