import asyncio
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from rss_parser import parse_rss
from llm_client import LLMClient, LLMConfig
from cache import SimpleCache
from db import store_article, list_articles
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="templates")

feed_cache = SimpleCache(ttl=600)

llm_config = LLMConfig.load()


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid RSS URL")
    return url


async def summarize_article(article: dict, llm: LLMClient) -> dict:
    prompt = (
        f"Title: {article['title']}\n\n{article['summary']}\n\n"
        "Provide a brief summary in 2-3 sentences."
    )
    summary = await asyncio.to_thread(llm.generate, prompt)
    result = {
        "title": article["title"],
        "link": article["link"],
        "summary": summary,
        "date": article.get("date", ""),
    }
    store_article(result["title"], result["link"], result["summary"], result["date"])
    return result


@app.get("/summarize")
async def summarize_rss(
    rss_url: str = Query(..., alias="rss_url"), model: Optional[str] = None
):
    validate_url(rss_url)

    articles = feed_cache.get(rss_url)
    if articles is None:
        articles = await asyncio.to_thread(parse_rss, rss_url)
        feed_cache.set(rss_url, articles)

    config = LLMConfig.load()
    if model:
        config.model_name = model

    summaries = []
    with LLMClient(config) as llm:
        tasks = [summarize_article(article, llm) for article in articles]
        summaries = await asyncio.gather(*tasks)

    return {"summaries": summaries}


@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/articles")


@app.get("/articles", response_class=HTMLResponse)
async def show_articles(request: Request):
    articles = list_articles()
    return templates.TemplateResponse(
        "articles.html", {"request": request, "articles": articles}
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
