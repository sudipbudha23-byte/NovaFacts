
import os
import re
import json
import time
import html
import hashlib
import tempfile
import calendar
import random

from pathlib import Path
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests
import feedparser

from deep_translator import GoogleTranslator


# ==================================================
# NOVAFACTS NEWS AUTOMATION
# Developed for NovaFacts
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FILE = BASE_DIR / "news.json"
CACHE_FILE = BASE_DIR / "translation_cache.json"

MAX_ITEMS = 60
MAX_AGE_DAYS = 30

RSS_TIMEOUT = 25
RSS_RETRIES = 3

TRANSLATION_RETRIES = 4
TRANSLATION_DELAY = 3.0
RETRY_BASE_DELAY = 8

MAX_TRANSLATION_LENGTH = 3500

CACHE_SAVE_INTERVAL = 1

USER_AGENT = (
    "Mozilla/5.0 "
    "(compatible; NovaFactsNewsBot/2.0)"
)


RSS_FEEDS = {
    "NASA": "https://www.nasa.gov/feed/",
    "NASA Science": "https://science.nasa.gov/feed/",
    "Phys.org": "https://phys.org/rss-feed/",
    "ScienceDaily": "https://www.sciencedaily.com/rss/all.xml",
    "arXiv Astronomy": "https://export.arxiv.org/rss/astro-ph",
    "arXiv Physics": "https://export.arxiv.org/rss/physics",
    "arXiv AI": "https://export.arxiv.org/rss/cs.AI",
}


# ==================================================
# HTTP SESSION
# ==================================================

session = requests.Session()

session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": (
        "application/rss+xml, "
        "application/xml, "
        "text/xml, "
        "*/*"
    )
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

    value = re.sub(
        r"<[^>]+>",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

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


def text_hash(text):
    return hashlib.sha256(
        clean_text(text).encode("utf-8")
    ).hexdigest()


# ==================================================
# SAFE JSON LOADING
# ==================================================

def load_json(path, default):

    try:

        if path.exists():

            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            return data

    except Exception as error:

        log(
            f"Could not read {path.name}: {error}"
        )

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

        os.replace(
            temp_path,
            path
        )

        return True

    except Exception as error:

        log(
            f"Could not save {path.name}: {error}"
        )

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
# TRANSLATION CACHE
# ==================================================

def load_translation_cache():

    cache = load_json(
        CACHE_FILE,
        {}
    )

    if not isinstance(cache, dict):
        return {}

    return cache


def get_cached_translation(text, cache):

    key = text_hash(text)

    value = cache.get(key)

    if isinstance(value, str) and value.strip():
        return value

    return ""


def save_cache(cache):

    return save_json_atomic(
        CACHE_FILE,
        cache
    )


# ==================================================
# DATE HANDLING
# ==================================================

def get_date(entry):

    try:

        if entry.get("published_parsed"):

            return datetime.fromtimestamp(
                calendar.timegm(
                    entry.published_parsed
                ),
                tz=timezone.utc
            ).isoformat()

        if entry.get("updated_parsed"):

            return datetime.fromtimestamp(
                calendar.timegm(
                    entry.updated_parsed
                ),
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

        log(
            f"Date parsing warning: {error}"
        )

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

        return parsed.astimezone(
            timezone.utc
        )

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
        "large language model",
        "computer vision",
        "ai model"
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
        "earthquake"
    ],

    "Biology": [
        "biology",
        "cell",
        "animal",
        "plant",
        "genetic",
        "genome",
        "evolution",
        "microbe",
        "bacteria"
    ],

    "Physics": [
        "physics",
        "quantum",
        "particle",
        "energy",
        "electricity",
        "magnetism",
        "relativity",
        "photon"
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
        "exoplanet"
    ]
}


def get_category(text):

    text = text.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():

        if any(
            word in text
            for word in keywords
        ):

            return category

    return "Science"


# ==================================================
# RSS COLLECTION WITH RETRIES
# ==================================================

def fetch_feed(source, feed_url):

    for attempt in range(
        1,
        RSS_RETRIES + 1
    ):

        try:

            response = session.get(
                feed_url,
                timeout=RSS_TIMEOUT
            )

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            if getattr(feed, "bozo", False):

                log(
                    f"RSS format warning: {source}"
                )

            if not feed.entries:

                log(
                    f"No entries found: {source}"
                )

                return []

            log(
                f"{source}: "
                f"{len(feed.entries)} entries found"
            )

            return feed.entries

        except requests.RequestException as error:

            log(
                f"RSS attempt {attempt}/"
                f"{RSS_RETRIES} failed [{source}]: {error}"
            )

        except Exception as error:

            log(
                f"Feed error [{source}]: {error}"
            )

        if attempt < RSS_RETRIES:

            delay = 3 * attempt

            log(
                f"Retrying {source} in {delay} seconds..."
            )

            time.sleep(delay)

    return []


def collect_news(old_news):

    collected = {}

    successful_feeds = 0

    log("Starting RSS collection...")

    for source, feed_url in RSS_FEEDS.items():

        entries = fetch_feed(
            source,
            feed_url
        )

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

            url = str(
                entry.get("link", "")
            ).strip()

            if not title or not valid_url(url):
                continue

            if url in collected:
                continue

            previous = old_news.get(
                url,
                {}
            )

            article = {
                "title": title,
                "summary": summary,
                "url": url,
                "source": source,

                "category": get_category(
                    title + " " + summary
                ),

                "published": get_date(entry),

                "title_ne": "",
                "summary_ne": ""
            }

            # Preserve old translations
            # when original text is unchanged.

            if previous.get("title") == title:

                article["title_ne"] = (
                    previous.get("title_ne", "")
                )

            if previous.get("summary") == summary:

                article["summary_ne"] = (
                    previous.get("summary_ne", "")
                )

            # If the current feed has no date,
            # preserve the previous date.

            if not article["published"]:

                article["published"] = (
                    previous.get("published", "")
                )

            collected[url] = article

        # Small delay between RSS sources.
        time.sleep(1)

    log(
        f"RSS collection completed. "
        f"Successful feeds: {successful_feeds}"
    )

    return collected, successful_feeds


# ==================================================
# TEXT CHUNKING
# ==================================================

def split_text(text):

    text = clean_text(text)

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?।])\s+",
        text
    )

    chunks = []

    current = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if len(sentence) > MAX_TRANSLATION_LENGTH:

            if current:

                chunks.append(current)
                current = ""

            words = sentence.split()

            temporary = ""

            for word in words:

                candidate = (
                    temporary + " " + word
                ).strip()

                if len(candidate) <= MAX_TRANSLATION_LENGTH:

                    temporary = candidate

                else:

                    if temporary:
                        chunks.append(temporary)

                    temporary = word

            if temporary:
                chunks.append(temporary)

            continue

        candidate = (
            current + " " + sentence
        ).strip()

        if len(candidate) <= MAX_TRANSLATION_LENGTH:

            current = candidate

        else:

            if current:
                chunks.append(current)

            current = sentence

    if current:
        chunks.append(current)

    return chunks


# ==================================================
# NEPALI TRANSLATION WITH RETRIES
# ==================================================

def translate_chunk(text):

    for attempt in range(
        1,
        TRANSLATION_RETRIES + 1
    ):

        try:

            translator = GoogleTranslator(
                source="auto",
                target="ne"
            )

            result = translator.translate(text)

            result = clean_text(result)

            if not result:

                raise ValueError(
                    "Translation returned an empty result"
                )

            # Slow down successful requests.
            time.sleep(TRANSLATION_DELAY)

            return result

        except Exception as error:

            log(
                f"Translation attempt "
                f"{attempt}/{TRANSLATION_RETRIES} failed: "
                f"{error}"
            )

            if attempt < TRANSLATION_RETRIES:

                delay = (
                    RETRY_BASE_DELAY
                    * (2 ** (attempt - 1))
                )

                delay += random.uniform(1, 3)

                log(
                    f"Waiting {delay:.1f} seconds before retry..."
                )

                time.sleep(delay)

    return ""


def translate_to_nepali(text):

    text = clean_text(text)

    if not text:
        return ""

    chunks = split_text(text)

    if not chunks:
        return ""

    translated_chunks = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):

        log(
            f"Translating part "
            f"{index}/{len(chunks)}"
        )

        translated = translate_chunk(chunk)

        if not translated:

            log(
                "Translation incomplete. "
                "Keeping original text."
            )

            return ""

        translated_chunks.append(
            translated
        )

    return " ".join(
        translated_chunks
    ).strip()


# ==================================================
# TRANSLATION WITH CACHE
# ==================================================

def translate_with_cache(
    text,
    cache,
    label
):

    text = clean_text(text)

    if not text:
        return ""

    key = text_hash(text)

    cached = get_cached_translation(
        text,
        cache
    )

    if cached:

        log(
            f"Cache hit: {label[:60]}"
        )

        return cached

    log(
        f"New translation: {label[:60]}"
    )

    translated = translate_to_nepali(text)

    if translated:

        cache[key] = translated

        # Save immediately after successful translation.
        save_cache(cache)

    return translated


# ==================================================
# KEEP RECENT OLD ARTICLES
# ==================================================

def merge_old_articles(
    new_articles,
    old_news
):

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

        # Keep unknown dates.
        # Remove only confirmed old articles.

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
# MAIN TRANSLATION PROCESS
# ==================================================

def process_translations(
    articles,
    cache
):

    total = len(articles)

    for index, article in enumerate(
        articles,
        start=1
    ):

        log(
            f"Article {index}/{total}: "
            f"{article.get('title', '')[:60]}"
        )

        # Translate title only if missing.

        if not article.get("title_ne"):

            article["title_ne"] = (
                translate_with_cache(
                    article.get("title", ""),
                    cache,
                    article.get("title", "")
                )
            )

        # Translate summary only if missing.

        if not article.get("summary_ne"):

            article["summary_ne"] = (
                translate_with_cache(
                    article.get("summary", ""),
                    cache,
                    article.get("title", "")
                )
            )

        # Save cache periodically as extra protection.

        if index % CACHE_SAVE_INTERVAL == 0:

            save_cache(cache)

        # Delay between articles.

        time.sleep(TRANSLATION_DELAY)


# ==================================================
# STATISTICS
# ==================================================

def get_statistics(articles):

    total = len(articles)

    translated_titles = sum(
        bool(item.get("title_ne"))
        for item in articles
    )

    translated_summaries = sum(
        bool(item.get("summary_ne"))
        for item in articles
    )

    complete = sum(
        bool(item.get("title_ne"))
        and (
            not item.get("summary")
            or bool(item.get("summary_ne"))
        )
        for item in articles
    )

    return {
        "total": total,
        "translated_titles": translated_titles,
        "translated_summaries": translated_summaries,
        "fully_translated": complete
    }


# ==================================================
# MAIN
# ==================================================

def main():

    log("===================================")
    log("NovaFacts News Automation Started")
    log("===================================")

    old_news = load_old_news()

    cache = load_translation_cache()

    log(
        f"Old articles loaded: {len(old_news)}"
    )

    log(
        f"Translation cache loaded: {len(cache)}"
    )

    # Collect RSS news.

    new_articles, successful_feeds = collect_news(
        old_news
    )

    # Never overwrite news if every feed fails.

    if successful_feeds == 0:

        log(
            "All RSS feeds failed. "
            "Keeping existing news.json."
        )

        return

    # Merge new and recent old articles.

    articles = merge_old_articles(
        new_articles,
        old_news
    )

    if not articles:

        log("No articles available.")
        return

    log(
        f"Articles selected: {len(articles)}"
    )

    # Translate only missing translations.

    process_translations(
        articles,
        cache
    )

    stats = get_statistics(
        articles
    )

    output = {

        "updated_at": utc_now().isoformat(),

        "article_count": stats["total"],

        "translated_count": stats["fully_translated"],

        "translation_stats": stats,

        "articles": articles,

        "note": (
            "News titles and summaries are collected "
            "from external RSS sources. Nepali text is "
            "machine translated and should be reviewed. "
            "Read each story at its original publisher."
        )
    }

    # Save final news JSON.

    news_saved = save_json_atomic(
        OUTPUT_FILE,
        output
    )

    # Save final translation cache.

    cache_saved = save_cache(
        cache
    )

    log("===================================")

    if news_saved:

        log(
            "News JSON saved successfully."
        )

    else:

        log(
            "ERROR: News JSON could not be saved."
        )

    if cache_saved:

        log(
            "Translation cache saved successfully."
        )

    else:

        log(
            "WARNING: Translation cache could not be saved."
        )

    log(
        f"Total articles: {stats['total']}"
    )

    log(
        f"Translated titles: "
        f"{stats['translated_titles']}"
    )

    log(
        f"Translated summaries: "
        f"{stats['translated_summaries']}"
    )

    log(
        f"Fully translated: "
        f"{stats['fully_translated']}"
    )

    log(
        f"Cache entries: {len(cache)}"
    )

    log(
        "NovaFacts update completed."
    )

    log("===================================")


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        log(
            "Process stopped by user (Ctrl+C)."
        )

    except Exception as error:

        log(
            f"Unexpected error: {error}"
        )

    finally:

        session.close()
