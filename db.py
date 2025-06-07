import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).resolve().parent / "articles.db"

_conn = None

def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                summary TEXT,
                date TEXT,
                hash TEXT UNIQUE
            )
            """
        )
        _conn.commit()
    return _conn

def compute_hash(title: str, date: str) -> str:
    return hashlib.sha256(f"{title}{date}".encode("utf-8")).hexdigest()

def store_article(title: str, link: str, summary: str, date: str) -> bool:
    conn = get_conn()
    h = compute_hash(title, date)
    try:
        conn.execute(
            "INSERT INTO articles (title, link, summary, date, hash) VALUES (?, ?, ?, ?, ?)",
            (title, link, summary, date, h),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def list_articles() -> List[Dict[str, str]]:
    conn = get_conn()
    cur = conn.execute(
        "SELECT title, link, summary, date FROM articles ORDER BY id DESC"
    )
    rows = cur.fetchall()
    return [
        {"title": row[0], "link": row[1], "summary": row[2], "date": row[3]}
        for row in rows
    ]
