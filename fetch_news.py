
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "news.json"
MAX_ITEMS = 60

FEEDS = [
    ("NASA", "Space", "https://www.nasa.gov/feed/"),
    ("NASA Science", "Space", "https://science.nasa.gov/feed/"),
    ("Phys.org", "Science", "https://phys.org/rss-feed/"),
    ("ScienceDaily", "Science", "https://www.sciencedaily.com/rss/all.xml"),
    ("arXiv Astrophysics", "Space", "https://export.arxiv.org/rss/astro-ph"),
    ("arXiv Physics", "Physics", "https://export.arxiv.org/rss/physics"),
    ("arXiv AI", "AI", "https://export.arxiv.org/rss/cs.AI"),
]

HEADERS = {"User-Agent": "NovaFactsScienceFeed/1.0"}

def clean_html(value):
    value = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\\s+", " ", value).strip()

def get_date(entry):
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc).isoformat()
            except Exception:
                pass
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            try:
                return datetime.fromtimestamp(
                    time.mktime(parsed), timezone.utc
                ).isoformat()
            except Exception:
                pass
    return ""

def valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def classify(title, summary, default):
    text = f"{title} {summary}".lower()
    if re.search(r"artificial intelligence|\\bai\\b|robot|machine learning", text):
        return "AI"
    if re.search(r"climate|ocean|earth|wildlife|environment|weather", text):
        return "Earth"
    if re.search(r"dna|gene|cell|biology|species|brain|medical|health", text):
        return "Biology"
    if re.search(r"quantum|particle|physics|gravity|fusion|energy|laser", text):
        return "Physics"
    if re.search(r"space|nasa|planet|galaxy|astronom|black hole|moon|mars|cosmos", text):
        return "Space"
    return default if default in {"Space", "Physics", "AI", "Biology", "Earth"} else "Science"

def main():
    found = {}
    successful_feeds = 0

    for source, default_category, feed_url in FEEDS:
        try:
            response = requests.get(feed_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            if not feed.entries:
                print(f"[WARN] No entries from {source}")
                continue

            successful_feeds += 1

            for entry in feed.entries:
                title = clean_html(entry.get("title", ""))
                url = (entry.get("link") or "").strip()

                if not title or not valid_url(url):
                    continue

                summary = clean_html(
                    entry.get("summary") or entry.get("description") or ""
                )
                summary = summary[:417] + "..." if len(summary) > 420 else summary
                published = get_date(entry)
                key = url.split("#", 1)[0].rstrip("/")

                found[key] = {
                    "title": title[:240],
                    "summary": summary,
                    "url": url,
                    "source": source,
                    "category": classify(title, summary, default_category),
                    "published": published,
                }

        except Exception as error:
            print(f"[WARN] {source} feed failed: {error}")

    if successful_feeds == 0 and OUTPUT.exists():
        print("[ERROR] All feeds failed. Keeping the previous news.json.")
        return

    articles = sorted(
        found.values(),
        key=lambda item: item.get("published") or "",
        reverse=True
    )[:MAX_ITEMS]

    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "article_count": len(articles),
        "articles": articles,
        "note": "Read and verify each story at its original source."
    }

    OUTPUT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\\n",
        encoding="utf-8"
    )
    print(f"[OK] Saved {len(articles)} articles from {successful_feeds} feeds.")

if __name__ == "__main__":
    main()
