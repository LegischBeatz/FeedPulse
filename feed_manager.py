import asyncio
import logging
from configparser import ConfigParser
from pathlib import Path
from typing import List, Tuple

from rss_parser import parse_rss, DEFAULT_LIMIT
from db import (
    store_processed_article,
    store_rewritten_article,
    compute_hash,
    get_rewritten_article,
)
from llm_client import LLMClient, LLMConfig


CONFIG_PATH = Path(__file__).resolve().parent / "config.ini"


def load_feed_config(path: Path = CONFIG_PATH) -> Tuple[List[str], int]:
    parser = ConfigParser(interpolation=None)
    read = parser.read(path)
    if not read:
        raise FileNotFoundError(f"Config file not found: {path}")

    feeds: List[str] = []
    if parser.has_option("RSS", "feeds"):
        raw = parser.get("RSS", "feeds")
        for line in raw.splitlines():
            for part in line.split(','):
                url = part.strip()
                if url:
                    feeds.append(url)

    interval = parser.getint("RSS", "interval", fallback=3600)
    return feeds, interval


async def rewrite_and_store(
    article: dict, llm: LLMClient, source: str, prompt_template: str
) -> None:
    try:
        if not store_processed_article(article["title"], article["link"], article.get("date", "")):
            logging.debug("Duplicate article skipped from %s: %s", source, article["title"])
            return

        prompt = prompt_template.format(title=article["title"], summary=article["summary"])
        rewritten = await asyncio.to_thread(llm.generate, prompt)
        store_rewritten_article(article["title"], article["link"], rewritten, article.get("date", ""))
        logging.info("Stored rewritten article from %s: %s", source, article["title"])
    except Exception as exc:
        logging.error("Failed to rewrite %s from %s: %s", article.get("title"), source, exc)


async def fetch_and_store(url: str) -> None:
    try:
        articles = await asyncio.to_thread(parse_rss, url, DEFAULT_LIMIT)
        if len(articles) < DEFAULT_LIMIT:
            logging.warning("%s returned %d articles", url, len(articles))
        else:
            logging.info("Fetched %d articles from %s", len(articles), url)

        config = LLMConfig.load()
        with LLMClient(config) as llm:
            tasks = [
                rewrite_and_store(art, llm, url, config.rewrite_prompt)
                for art in articles
            ]
            if tasks:
                await asyncio.gather(*tasks)
    except Exception as exc:
        logging.error("Failed to process %s: %s", url, exc)


async def run_async(config_path: Path = CONFIG_PATH) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Feed manager started")
    while True:
        feeds, interval = load_feed_config(config_path)
        if not feeds:
            logging.warning("No feeds configured")
        tasks = [fetch_and_store(url) for url in feeds]
        if tasks:
            await asyncio.gather(*tasks)
        logging.info("Waiting %s seconds before next fetch", interval)
        await asyncio.sleep(interval)


def run(config_path: Path = CONFIG_PATH) -> None:
    asyncio.run(run_async(config_path))


if __name__ == "__main__":
    run()
