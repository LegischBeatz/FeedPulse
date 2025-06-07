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
                hash TEXT UNIQUE
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


def store_rewritten_article(title: str, link: str, content: str, date: str) -> bool:
    conn = get_conn()
    h = compute_hash(title, date)
    try:
        conn.execute(
            "INSERT INTO rewritten_articles (title, link, content, date, hash) VALUES (?, ?, ?, ?, ?)",
            (title, link, content, date, h),
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
        "SELECT title, link, content, date FROM rewritten_articles ORDER BY id DESC"
    )
    rows = cur.fetchall()
    return [
        {"title": row[0], "link": row[1], "content": row[2], "date": row[3]}
        for row in rows
    ]
