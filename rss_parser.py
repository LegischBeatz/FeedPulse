import feedparser
import requests
from typing import List, Dict, Tuple, Optional


# Number of articles returned when no explicit limit is provided
DEFAULT_LIMIT = 5

def _get_date(entry) -> str:
    for key in ("published", "updated", "created", "pubDate"):
        if key in entry:
            return str(entry.get(key))
    return ""

def parse_rss(
    url: str,
    limit: int = DEFAULT_LIMIT,
    data: Optional[bytes] = None,
) -> List[Dict[str, str]]:
    feed = feedparser.parse(data if data is not None else url)
    articles: List[Dict[str, str]] = []
    for entry in feed.entries[:limit]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if "summary" in entry else "",
            "date": _get_date(entry),
        })
    return articles


def validate_feed(url: str, timeout: int = 10) -> Tuple[bool, str, Optional[bytes]]:
    """Check if the given RSS feed is accessible and valid.

    Returns a tuple of success flag, reason string and the fetched content if
    successful.
    """
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "FeedPulse"})
        resp.raise_for_status()
        content = resp.content
        parsed = feedparser.parse(content)
        if parsed.bozo:
            return False, str(parsed.bozo_exception), None
        if not parsed.entries:
            return False, "No entries found", None
        return True, "ok", content
    except Exception as exc:
        return False, str(exc), None
