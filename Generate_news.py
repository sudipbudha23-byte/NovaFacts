
import os
import re
import json
import time
import html
import tempfile
import calendar

from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, quote_plus

import requests
import feedparser


# ==================================================
# NOVAFACTS NEWS AUTOMATION
# English + Native Nepali RSS News
# No Google Translate required
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "news.json"

MAX_ITEMS = 80
MAX_AGE_DAYS = 30

RSS_TIMEOUT = 25
RSS_RETRIES = 3

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; NovaFactsNewsBot/5.0)"
)


# ==================================================
# ENGLISH RSS SOURCES
# ==================================================

ENGLISH_FEEDS = {
    "NASA": "https://www.nasa.gov/feed/",
    "NASA Science": "https://science.nasa.gov/feed/",
    "Phys.org": "https://phys.org/rss-feed/",
    "ScienceDaily": "https://www.sciencedaily.com/rss/all.xml",
    "arXiv Astronomy": "https://export.arxiv.org/rss/astro-ph",
    "arXiv Physics": "https://export.arxiv.org/rss/physics",
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",
}


# ==================================================
# NEPALI GOOGLE NEWS RSS SOURCES
# ==================================================

NEPALI_TOPICS = {
    "नेपाली विज्ञान समाचार": "विज्ञान OR वैज्ञानिक खोज",
    "नेपाली अन्तरिक्ष समाचार": "अन्तरिक्ष OR खगोल विज्ञान OR NASA",
    "नेपाली प्रविधि समाचार": "प्रविधि OR कृत्रिम बुद्धिमत्ता OR AI",
    "नेपाली वातावरण समाचार": "वातावरण OR जलवायु परिवर्तन OR पृथ्वी",
    "नेपाली जीवविज्ञान समाचार": "जीवविज्ञान OR वन्यजन्तु OR जीव",
    "नेपाली भौतिक विज्ञान समाचार": "भौतिक विज्ञान OR क्वान्टम OR ऊर्जा",
}


def create_nepali_feed_url(query):
    encoded_query = quote_plus(query)

    return (
        "https://news.google.com/rss/search?q="
        + encoded_query
        + "&hl=ne&gl=NP&ceid=NP:ne"
    )


NEPALI_FEEDS = {
    source: create_nepali_feed_url(query)
    for source, query in NEPALI_TOPICS.items()
}


# ==================================================
# HTTP SESSION
# ==================================================

session = requests.Session()

session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
})


# ==================================================
# GENERAL UTILITIES
# ==================================================

def utc_now():
    return datetime.now(timezone.utc)


def log(message):
    print(
        f"[{utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}] "
        f"{message}",
        flush=True
    )


def clean_text(value):
    value = html.unescape(str(value or ""))

    value = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        value,
        flags=re.I | re.S
    )

    value = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        value,
        flags=re.I | re.S
    )

    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def valid_url(url):
    try:
        parsed = urlparse(str(url))

        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
        )

    except Exception:
        return False


# ==================================================
# SAFE JSON
# ==================================================

def load_json(path, default):
    try:
        if path.exists():
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            return data

    except Exception as error:
        log(f"Could not read {path.name}: {error}")

    return default


def save_json_atomic(path, data):
    temp_path = None

    try:
        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=BASE_DIR,
            delete=False,
            suffix=".tmp"
        ) as temp:

            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())

            temp_path = Path(temp.name)

        os.replace(temp_path, path)

        return True

    except Exception as error:
        log(f"Could not save {path.name}: {error}")

        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

        return False


# ==================================================
# LOAD OLD NEWS
# ==================================================

def load_old_news():
    data = load_json(
        OUTPUT_FILE,
        {"articles": []}
    )

    if not isinstance(data, dict):
        return {}

    articles = data.get("articles", [])

    if not isinstance(articles, list):
        return {}

    old_news = {}

    for item in articles:
        if not isinstance(item, dict):
            continue

        url = item.get("url")

        if url and valid_url(url):
            old_news[url] = item

    return old_news


# ==================================================
# DATE HANDLING
# ==================================================

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

        for key in ("published", "updated"):
            value = entry.get(key)

            if value:
                parsed = parsedate_to_datetime(value)

                if parsed.tzinfo is None:
                    parsed = parsed.replace(
                        tzinfo=timezone.utc
                    )

                return parsed.astimezone(
                    timezone.utc
                ).isoformat()

    except Exception as error:
        log(f"Date parsing warning: {error}")

    return ""


def parse_iso_date(value):
    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(timezone.utc)

    except Exception:
        return None


# ==================================================
# CATEGORY DETECTION
# ==================================================

CATEGORY_KEYWORDS = {
    "AI": [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "neural network",
        "robot",
        "chatgpt",
        "कृत्रिम बुद्धिमत्ता",
        "एआई",
        "रोबोट"
    ],

    "Earth": [
        "earth",
        "climate",
        "environment",
        "ocean",
        "forest",
        "pollution",
        "weather",
        "volcano",
        "earthquake",
        "पृथ्वी",
        "वातावरण",
        "जलवायु",
        "भूकम्प"
    ],

    "Biology": [
        "biology",
        "cell",
        "animal",
        "plant",
        "genetic",
        "genome",
        "evolution",
        "bacteria",
        "जीवविज्ञान",
        "वन्यजन्तु",
        "वनस्पति"
    ],

    "Physics": [
        "physics",
        "quantum",
        "particle",
        "energy",
        "electricity",
        "magnetism",
        "relativity",
        "भौतिक विज्ञान",
        "क्वान्टम",
        "ऊर्जा"
    ],

    "Space": [
        "space",
        "planet",
        "nasa",
        "moon",
        "mars",
        "galaxy",
        "black hole",
        "astronomy",
        "star",
        "universe",
        "अन्तरिक्ष",
        "खगोल",
        "ग्रह",
        "आकाशगंगा",
        "चन्द्रमा"
    ]
}


def get_category(text):
    text = text.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in text for word in keywords):
            return category

    return "Science"


# ==================================================
# RSS COLLECTION
# ==================================================

def fetch_feed(source, feed_url):
    for attempt in range(1, RSS_RETRIES + 1):

        try:
            response = session.get(
                feed_url,
                timeout=RSS_TIMEOUT
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if getattr(feed, "bozo", False):
                log(f"RSS format warning: {source}")

            if not feed.entries:
                log(f"No entries found: {source}")
                return []

            log(
                f"{source}: {len(feed.entries)} entries found"
            )

            return feed.entries

        except requests.RequestException as error:
            log(
                f"RSS attempt {attempt}/{RSS_RETRIES} "
                f"failed [{source}]: {error}"
            )

        except Exception as error:
            log(f"Feed error [{source}]: {error}")

        if attempt < RSS_RETRIES:
            delay = 3 * attempt

            log(
                f"Retrying {source} in {delay} seconds..."
            )

            time.sleep(delay)

    return []


# ==================================================
# COLLECT ENGLISH AND NEPALI NEWS
# ==================================================

def collect_news(old_news):
    collected = {}
    successful_feeds = 0

    english_count = 0
    nepali_count = 0

    log("Starting English RSS collection...")

    all_feeds = []

    for source, url in ENGLISH_FEEDS.items():
        all_feeds.append((source, url, "en"))

    for source, url in NEPALI_FEEDS.items():
        all_feeds.append((source, url, "ne"))

    for source, feed_url, language in all_feeds:

        entries = fetch_feed(source, feed_url)

        if entries:
            successful_feeds += 1

        for entry in entries:

            title = clean_text(
                entry.get("title", "")
            )

            summary = clean_text(
                entry.get(
                    "summary",
                    entry.get("description", "")
                )
            )

            if not summary and entry.get("content"):
                try:
                    summary = clean_text(
                        entry["content"][0].get("value", "")
                    )
                except (IndexError, AttributeError, TypeError):
                    summary = ""

            url = str(
                entry.get("link", "")
            ).strip()

            if not title or not valid_url(url):
                continue

            if url in collected:
                continue

            previous = old_news.get(url, {})

            article = {
                "title": title,
                "summary": summary,
                "url": url,
                "source": source,
                "category": get_category(
                    title + " " + summary
                ),
                "published": (
                    get_date(entry)
                    or previous.get("published", "")
                ),
                "language": language,
                "title_ne": "",
                "summary_ne": ""
            }

            if language == "ne":
                # These are original Nepali RSS texts.
                article["title_ne"] = title
                article["summary_ne"] = summary
                nepali_count += 1

            else:
                # Preserve any old English article translations.
                if previous.get("title") == title:
                    article["title_ne"] = (
                        previous.get("title_ne", "")
                    )

                if previous.get("summary") == summary:
                    article["summary_ne"] = (
                        previous.get("summary_ne", "")
                    )

                english_count += 1

            collected[url] = article

        time.sleep(1)

    log(f"English articles collected: {english_count}")
    log(f"Nepali articles collected: {nepali_count}")

    log(
        f"RSS collection completed. "
        f"Successful feeds: {successful_feeds}"
    )

    return collected, successful_feeds


# ==================================================
# STATISTICS
# ==================================================

def get_statistics(articles):
    total = len(articles)

    nepali_articles = sum(
        item.get("language") == "ne"
        for item in articles
    )

    english_articles = sum(
        item.get("language") == "en"
        for item in articles
    )

    nepali_titles = sum(
        bool(item.get("title_ne"))
        for item in articles
    )

    nepali_summaries = sum(
        bool(item.get("summary_ne"))
        for item in articles
    )

    return {
        "total": total,
        "english_articles": english_articles,
        "nepali_articles": nepali_articles,
        "nepali_titles": nepali_titles,
        "nepali_summaries": nepali_summaries
    }


# ==================================================
# SAVE NEWS
# ==================================================

def save_news(articles):
    stats = get_statistics(articles)

    output = {
        "updated_at": utc_now().isoformat(),
        "article_count": stats["total"],
        "nepali_count": stats["nepali_articles"],
        "english_count": stats["english_articles"],
        "news_stats": stats,
        "articles": articles,
        "note": (
            "English articles are collected from their "
            "original English RSS publishers. Nepali "
            "articles are collected directly from Nepali "
            "language RSS search results. Nepali articles "
            "are not machine translated. Read full stories "
            "at their original publishers."
        )
    }

    saved = save_json_atomic(
        OUTPUT_FILE,
        output
    )

    if saved:
        log("news.json saved successfully.")

    return saved


# ==================================================
# MERGE OLD AND NEW ARTICLES
# ==================================================

def merge_old_articles(new_articles, old_news):
    merged = dict(old_news)
    merged.update(new_articles)

    cutoff = utc_now() - timedelta(
        days=MAX_AGE_DAYS
    )

    result = []

    for url, article in merged.items():

        if not valid_url(url):
            continue

        published = parse_iso_date(
            article.get("published", "")
        )

        if published and published < cutoff:
            continue

        result.append(article)

    result.sort(
        key=lambda item: (
            parse_iso_date(
                item.get("published", "")
            ) or datetime.min.replace(
                tzinfo=timezone.utc
            )
        ),
        reverse=True
    )

    return result[:MAX_ITEMS]


# ==================================================
# MAIN
# ==================================================

def main():
    log("===================================")
    log("NovaFacts News Automation Started")
    log("English + Nepali RSS Mode")
    log("===================================")

    old_news = load_old_news()

    log(f"Old articles loaded: {len(old_news)}")

    new_articles, successful_feeds = collect_news(
        old_news
    )

    # Never overwrite existing news if every feed fails.
    if successful_feeds == 0:
        log(
            "All RSS feeds failed. "
            "Keeping existing news.json."
        )
        return

    articles = merge_old_articles(
        new_articles,
        old_news
    )

    if not articles:
        log("No articles available.")
        return

    log(f"Articles selected: {len(articles)}")

    save_news(articles)

    stats = get_statistics(articles)

    log("===================================")
    log(f"Total articles: {stats['total']}")
    log(
        f"English articles: "
        f"{stats['english_articles']}"
    )
    log(
        f"Nepali articles: "
        f"{stats['nepali_articles']}"
    )
    log(
        f"Nepali titles available: "
        f"{stats['nepali_titles']}"
    )
    log(
        f"Nepali summaries available: "
        f"{stats['nepali_summaries']}"
    )
    log("===================================")
    log("NovaFacts update completed.")


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        log(
            "Process stopped by user. "
            "Previously saved news is preserved."
        )

    except Exception as error:
        log(f"Unexpected error: {error}")

    finally:
        session.close()
