import feedparser

def _get_date(entry) -> str:
    for key in ("published", "updated", "created", "pubDate"):
        if key in entry:
            return str(entry.get(key))
    return ""

def parse_rss(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:5]:  # Limiting to latest 5 entries
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary if 'summary' in entry else '',
            'date': _get_date(entry),
        })
    return articles
