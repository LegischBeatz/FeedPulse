from fastapi import FastAPI
from rss_parser import parse_rss
from llm_client import LLMClient, LLMConfig

app = FastAPI()

llm_config = LLMConfig.load()

@app.get("/summarize")
def summarize_rss(rss_url: str):
    articles = parse_rss(rss_url)
    summaries = []

    with LLMClient(llm_config) as llm:
        for article in articles:
            prompt = f"Summarize briefly: {article['title']} - {article['summary']}"
            summary = llm.generate(prompt)
            summaries.append({
                'title': article['title'],
                'link': article['link'],
                'summary': summary
            })

    return {"summaries": summaries}
