import feedparser
from typing import List, Dict


DEFAULT_LIMIT = 10

def _get_date(entry) -> str:
    for key in ("published", "updated", "created", "pubDate"):
        if key in entry:
            return str(entry.get(key))
    return ""

def parse_rss(url: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, str]]:
    feed = feedparser.parse(url)
    articles: List[Dict[str, str]] = []
    for entry in feed.entries[:limit]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if "summary" in entry else "",
            "date": _get_date(entry),
        })
    return articles
