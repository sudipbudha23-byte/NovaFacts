
import json
import re
import time
import calendar
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
from deep_translator import GoogleTranslator

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "news.json"

MAX_ITEMS = 60

RSS_FEEDS = {
    "NASA": "https://www.nasa.gov/feed/",
    "NASA Science": "https://science.nasa.gov/feed/",
    "Phys.org": "https://phys.org/rss-feed/",
    "ScienceDaily": "https://www.sciencedaily.com/rss/all.xml",
    "arXiv Astronomy": "https://export.arxiv.org/rss/astro-ph",
    "arXiv Physics": "https://export.arxiv.org/rss/physics",
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",
}


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = re.sub(r"&nbsp;|&#160;", " ", value)
    value = re.sub(r"&amp;", "&", value)
    value = re.sub(r"&quot;", '"', value)
    value = re.sub(r"&#39;|&apos;", "'", value)
    return re.sub(r"\s+", " ", value).strip()


def valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def get_date(entry):
    try:
        if entry.get("published_parsed"):
            return datetime.fromtimestamp(
                calendar.timegm(entry.published_parsed),
                tz=timezone.utc
            ).isoformat()

        if entry.get("updated_parsed"):
            return datetime.fromtimestamp(
                calendar.timegm(entry.updated_parsed),
                tz=timezone.utc
            ).isoformat()

        if entry.get("published"):
            return parsedate_to_datetime(
                entry.published
            ).astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    return datetime.now(timezone.utc).isoformat()


def get_category(text):
    text = text.lower()

    if any(x in text for x in ["artificial intelligence", "machine learning", "robot", "chatgpt", "ai model"]):
        return "AI"

    if any(x in text for x in ["earth", "climate", "environment", "ocean", "forest", "pollution"]):
        return "Earth"

    if any(x in text for x in ["biology", "cell", "animal", "plant", "genetic", "health"]):
        return "Biology"

    if any(x in text for x in ["physics", "quantum", "particle", "energy", "electricity"]):
        return "Physics"

    if any(x in text for x in ["space", "planet", "nasa", "moon", "mars", "galaxy", "black hole", "star"]):
        return "Space"

    return "Science"


def load_old_news():
    try:
        if OUTPUT_FILE.exists():
            data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            articles = data.get("articles", [])

            return {
                item.get("url"): item
                for item in articles
                if item.get("url")
            }
    except Exception as error:
        print("Old news could not be loaded:", error)

    return {}


def translate_to_nepali(text):
    text = clean_text(text)

    if not text:
        return ""

    try:
        translator = GoogleTranslator(source="auto", target="ne")
        result = translator.translate(text)
        return result.strip() if result else ""
    except Exception as error:
        print("Translation failed:", error)
        return ""


def main():
    old_news = load_old_news()
    collected = []
    seen_urls = set()

    print("NovaFacts: collecting RSS news...")

    for source, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                title = clean_text(entry.get("title", ""))
                summary = clean_text(
                    entry.get("summary", entry.get("description", ""))
                )
                url = entry.get("link", "").strip()

                if not title or not valid_url(url):
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                article = {
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "source": source,
                    "category": get_category(title + " " + summary),
                    "published": get_date(entry)
                }

                # Reuse existing translations whenever possible.
                previous = old_news.get(url, {})

                if previous.get("title_ne") and previous.get("summary_ne"):
                    article["title_ne"] = previous["title_ne"]
                    article["summary_ne"] = previous["summary_ne"]
                else:
                    print("Translating:", title[:65])

                    article["title_ne"] = translate_to_nepali(title)
                    time.sleep(0.4)

                    article["summary_ne"] = translate_to_nepali(summary)
                    time.sleep(0.4)

                collected.append(article)

        except Exception as error:
            print("Feed error:", source, error)

    if not collected:
        print("No news collected. Keeping the existing news.json.")
        return

    collected.sort(
        key=lambda item: item.get("published", ""),
        reverse=True
    )

    collected = collected[:MAX_ITEMS]

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(collected),
        "articles": collected,
        "note": "Read and verify each story at its original source."
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    translated_count = sum(
        1 for item in collected
        if item.get("title_ne") and item.get("summary_ne")
    )

    print("News saved successfully!")
    print("Total articles:", len(collected))
    print("Nepali translations:", translated_count)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
