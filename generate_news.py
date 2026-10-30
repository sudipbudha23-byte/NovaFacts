
import json
import re
import calendar
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests

# ========================================
# NOVAFACTS - SCIENCE NEWS COLLECTOR
# ========================================

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "news.json"

MAX_ITEMS = 60
HEADERS = {
    "User-Agent": "Mozilla/5.0 NovaFactsScienceFeed/1.0"
}

FEEDS = [
    ("NASA", "Space", "https://www.nasa.gov/feed/"),
    ("NASA Science", "Space", "https://science.nasa.gov/feed/"),
    ("Phys.org", "Science", "https://phys.org/rss-feed/"),
    ("ScienceDaily", "Science", "https://www.sciencedaily.com/rss/all.xml"),
    ("arXiv Astrophysics", "Space", "https://export.arxiv.org/rss/astro-ph"),
    ("arXiv Physics", "Physics", "https://export.arxiv.org/rss/physics"),
    ("arXiv AI", "AI", "https://export.arxiv.org/rss/cs.AI"),
]


def clean_html(value):
    """Remove HTML tags and extra spaces."""
    value = re.sub(
        r"(?is)<(script|style)\b[^>]*>.*?</\1>",
        " ",
        value or ""
    )

    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def get_date(entry):
    """Convert publication date to UTC ISO format."""

    for key in ("published", "updated"):
        raw = entry.get(key)

        if raw:
            try:
                dt = datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
                )

                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                return dt.astimezone(timezone.utc).isoformat()

            except (ValueError, TypeError):
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
                timestamp = calendar.timegm(parsed)
                dt = datetime.fromtimestamp(
                    timestamp,
                    timezone.utc
                )
                return dt.isoformat()

            except Exception:
                pass

    return ""


def valid_url(url):
    """Check whether the article URL is valid."""

    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in ("https", "http")
            and bool(parsed.netloc)
        )

    except Exception:
        return False


def classify(title, summary, default):
    """Automatically classify science articles."""

    text = f"{title} {summary}".lower()

    if re.search(
        r"artificial intelligence|machine learning|"
        r"\bai\b|robot|neural network",
        text
    ):
        return "AI"

    if re.search(
        r"climate|ocean|earth|wildlife|environment|weather",
        text
    ):
        return "Earth"

    if re.search(
        r"dna|gene|cell|biology|species|brain|medical|health",
        text
    ):
        return "Biology"

    if re.search(
        r"quantum|particle|physics|gravity|fusion|energy|laser",
        text
    ):
        return "Physics"

    if re.search(
        r"space|nasa|planet|galaxy|astronom|black hole|"
        r"moon|mars|cosmos",
        text
    ):
        return "Space"

    allowed = {
        "Space", "Physics", "AI",
        "Biology", "Earth", "Science"
    }

    return default if default in allowed else "Science"


def main():

    found = {}
    successful_feeds = 0

    print("\nNOVAFACTS NEWS COLLECTOR")
    print("=" * 40)

    for source, default_category, feed_url in FEEDS:

        try:
            print(f"[FETCH] {source}")

            response = requests.get(
                feed_url,
                headers=HEADERS,
                timeout=20
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if not feed.entries:
                print(f"[WARN] No entries from {source}")
                continue

            successful_feeds += 1

            for entry in feed.entries:

                title = clean_html(
                    entry.get("title", "")
                )

                url = (entry.get("link") or "").strip()

                if not title or not valid_url(url):
                    continue

                summary = clean_html(
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                )

                if len(summary) > 420:
                    summary = summary[:417] + "..."

                published = get_date(entry)

                key = url.split("#", 1)[0].rstrip("/")

                found[key] = {
                    "title": title[:240],
                    "summary": summary,
                    "url": url,
                    "source": source,
                    "category": classify(
                        title,
                        summary,
                        default_category
                    ),
                    "published": published
                }

            print(f"[OK] {source}: {len(feed.entries)} entries")

        except Exception as error:

            print(f"[WARN] {source} failed: {error}")

    # Keep previous file if every feed fails
    if successful_feeds == 0:
        print("\n[ERROR] All RSS feeds failed.")
        print("Previous news.json has not been changed.")
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
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print("\n" + "=" * 40)
    print(f"[SUCCESS] Saved {len(articles)} articles.")
    print(f"[FEEDS] Successful feeds: {successful_feeds}")
    print(f"[FILE] {OUTPUT}")
    print("=" * 40)


if __name__ == "__main__":
    main()
