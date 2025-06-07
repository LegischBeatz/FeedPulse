import feedparser

def parse_rss(url):
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries[:5]:  # Limiting to latest 5 entries
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'summary': entry.summary if 'summary' in entry else ''
        })
    return articles
