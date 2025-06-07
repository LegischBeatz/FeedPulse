import asyncio
import logging
from configparser import ConfigParser
from pathlib import Path
from typing import List, Tuple

from rss_parser import parse_rss, DEFAULT_LIMIT
from db import store_article


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


async def fetch_and_store(url: str) -> None:
    try:
        articles = await asyncio.to_thread(parse_rss, url, DEFAULT_LIMIT)
        if len(articles) < DEFAULT_LIMIT:
            logging.warning("%s returned %d articles", url, len(articles))
        else:
            logging.info("Fetched %d articles from %s", len(articles), url)
        for art in articles:
            stored = store_article(art["title"], art["link"], art["summary"], art["date"])
            if stored:
                logging.info("Stored article from %s: %s", url, art["title"])
            else:
                logging.debug("Duplicate article skipped from %s: %s", url, art["title"])
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
