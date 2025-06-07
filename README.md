# FeedPulse

FeedPulse is a modern RSS feed aggregation and summarization tool designed specifically for teams. It transforms RSS feeds into concise, blog-style summaries directly accessible via your browser, helping teams stay informed, organized, and aligned on the latest news and updates relevant to their workflow.

## Features

* **Automated Summaries**: FeedPulse automatically extracts key insights and summarizes RSS content into clear, concise blog-style articles.
* **Team Collaboration**: Share curated feeds and summaries easily within your team, ensuring everyone is up-to-date.
* **Browser-Friendly Interface**: Enjoy a clean, intuitive user interface optimized for easy readability and quick browsing.
* **Customizable Feeds**: Tailor your news feed experience by selecting and organizing specific RSS sources relevant to your team's interests.
* **Built-in Caching**: Recently fetched feeds are cached for faster responses.
* **Async Summaries**: Articles are summarized concurrently for improved performance.

## Use Cases

* **Daily Briefings**: Ideal for morning stand-ups or team briefings, providing quick insights on relevant industry news.
* **Market Research**: Efficiently track competitors, industry trends, and breaking news without sifting through extensive articles.
* **Knowledge Management**: Centralize important updates and maintain a single source of truth for team-wide news and information.

## Getting Started

Follow the steps below to set up and run FeedPulse locally.

### Installation

Clone the repository and install the required packages:

```bash
git clone https://github.com/yourusername/FeedPulse.git
cd FeedPulse
pip install -r requirements.txt
```

### Configuration

The application relies on a running language model service. Edit `config.ini` to
point `api_url` to your model's endpoint and specify the `model_name`. The
defaults work with an Ollama-compatible API.

### Running the API

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The server will listen on `http://localhost:8000` by default.

## Usage Guide

### Summarize a Feed

Send a GET request to `/summarize` with the RSS feed URL:

```bash
curl "http://localhost:8000/summarize?rss_url=https://example.com/feed.xml"
```

Optionally, specify a different model using the `model` query parameter:

```bash
curl "http://localhost:8000/summarize?rss_url=https://example.com/feed.xml&model=my-model"
```

The response contains a JSON array of article titles, links, dates and generated
summaries. Each request also stores the results in a local SQLite database.

### View Stored Articles

Open `http://localhost:8000/articles` in your browser to see previously
summarized articles rendered as a simple web page.

## Feed Manager

FeedPulse includes a helper script, `feed_manager.py`, for automatically
fetching and storing articles from multiple RSS feeds. Ensure you have installed
the dependencies listed in `requirements.txt` before running it. The default
`config.ini` lists several security news feeds which are fetched concurrently.

1. Edit `config.ini` and list your feeds under the `[RSS]` section. You can
   provide one feed URL per line or separate them with commas. Adjust the
   `interval` value to control how often the feeds are fetched.
2. Start the manager:

```bash
python feed_manager.py
```

The script runs continuously, polling the configured feeds and persisting new
articles to `articles.db`. Each cycle retrieves the ten most recent articles from
every feed and skips entries that already exist in the database.

## Contributing

We welcome contributions from the community! Feel free to submit issues, suggestions, or pull requests.

## License

FeedPulse is open-source and available under the [MIT License](LICENSE).
