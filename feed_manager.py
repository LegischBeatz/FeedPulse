import argparse
import asyncio
import logging
from configparser import ConfigParser
from pathlib import Path
from typing import List, Tuple

from rss_parser import parse_rss, DEFAULT_LIMIT, validate_feed
from db import (
    store_processed_article,
    store_rewritten_article,
    record_feed_status,
    get_failed_feeds,
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
        store_rewritten_article(
            article["title"],
            article["link"],
            rewritten,
            article.get("date", ""),
            None,
        )
        logging.info("Stored rewritten article from %s: %s", source, article["title"])
    except Exception as exc:
        logging.error("Failed to rewrite %s from %s: %s", article.get("title"), source, exc)


async def fetch_and_store(url: str) -> None:
    ok, reason, data = await asyncio.to_thread(validate_feed, url)
    record_feed_status(url, ok, reason)
    if not ok:
        logging.error("Skipping %s: %s", url, reason)
        return
    try:
        articles = await asyncio.to_thread(parse_rss, url, DEFAULT_LIMIT, data)
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


async def run_async(config_path: Path = CONFIG_PATH, loop: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Feed manager started")
    while True:
        feeds, interval = load_feed_config(config_path)
        if not feeds:
            logging.warning("No feeds configured")
        failed = set(get_failed_feeds())
        if failed:
            logging.info("Skipping %d failed feeds", len(failed))
        tasks = [fetch_and_store(url) for url in feeds if url not in failed]
        if tasks:
            await asyncio.gather(*tasks)
        if not loop:
            break
        logging.info("Waiting %s seconds before next fetch", interval)
        await asyncio.sleep(interval)


def run(config_path: Path = CONFIG_PATH, loop: bool = False) -> None:
    asyncio.run(run_async(config_path, loop))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and rewrite RSS feeds")
    parser.add_argument(
        "--config", type=Path, default=CONFIG_PATH, help="Path to configuration file"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously using the interval from the config file",
    )
    args = parser.parse_args()
    run(args.config, loop=args.loop)
