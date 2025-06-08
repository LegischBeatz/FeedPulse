import asyncio
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from typing import Optional

from rss_parser import parse_rss, DEFAULT_LIMIT
from llm_client import LLMClient, LLMConfig
from cache import SimpleCache
from db import (
    store_processed_article,
    store_rewritten_article,
    get_rewritten_article,
    list_rewritten_articles,
    list_rewritten_articles_with_id,
    delete_rewritten_articles,
    compute_hash,
)
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

feed_cache = SimpleCache(ttl=600)


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid RSS URL")
    return url


async def rewrite_article(article: dict, llm: LLMClient, prompt_template: str) -> dict:
    h = compute_hash(article["title"], article.get("date", ""))
    if not store_processed_article(article["title"], article["link"], article.get("date", "")):
        existing = get_rewritten_article(h)
        if existing:
            return existing

    prompt = prompt_template.format(title=article["title"], summary=article["summary"])
    rewritten = await asyncio.to_thread(llm.generate, prompt)
    result = {
        "title": article["title"],
        "link": article["link"],
        "content": rewritten,
        "date": article.get("date", ""),
    }
    store_rewritten_article(result["title"], result["link"], result["content"], result["date"])
    return result


@app.get("/summarize")
async def summarize_rss(
    rss_url: str = Query(..., alias="rss_url"),
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
):
    validate_url(rss_url)

    cache_key = f"{rss_url}:{limit}"
    articles = feed_cache.get(cache_key)
    if articles is None:
        articles = await asyncio.to_thread(parse_rss, rss_url, limit)
        feed_cache.set(cache_key, articles)

    config = LLMConfig.load()
    if model:
        config.model_name = model
    if prompt:
        config.rewrite_prompt = prompt

    results = []
    with LLMClient(config) as llm:
        tasks = [
            rewrite_article(article, llm, config.rewrite_prompt)
            for article in articles
        ]
        results = await asyncio.gather(*tasks)

    return {"articles": results}


@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/articles")


@app.get("/articles", response_class=HTMLResponse)
async def show_articles(request: Request):
    return templates.TemplateResponse(
        "articles.html", {"request": request}
    )


@app.get("/article_list", response_class=HTMLResponse)
async def article_list(request: Request):
    articles = list_rewritten_articles()
    return templates.TemplateResponse(
        "article_list.html", {"request": request, "articles": articles}
    )

@app.get("/api/articles")
async def api_articles():
    return {"articles": list_rewritten_articles()}


@app.get("/edit", response_class=HTMLResponse)
async def edit_articles(request: Request):
    articles = list_rewritten_articles_with_id()
    return templates.TemplateResponse(
        "edit.html", {"request": request, "articles": articles}
    )


@app.post("/edit")
async def delete_articles(ids: list[int] = Form(...)):
    delete_rewritten_articles(ids)
    return RedirectResponse(url="/edit", status_code=303)


@app.post("/delete/{article_id}")
async def delete_article(article_id: int):
    delete_rewritten_articles([article_id])
    return Response(status_code=204)



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

