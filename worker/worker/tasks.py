from . import app
from llm_client import LLMClient, LLMConfig
from rss_parser import parse_rss
from db import store_rewritten_article, store_processed_article, compute_hash

@app.task
def rewrite_feed_article(article: dict):
    config = LLMConfig.load()
    with LLMClient(config) as llm:
        prompt = config.rewrite_prompt.format(title=article['title'], summary=article['summary'])
        result = llm.generate(prompt)
    store_processed_article(article['title'], article['link'], article.get('date', ''))
    store_rewritten_article(article['title'], article['link'], result, article.get('date', ''))

