import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis
from celery import shared_task
from django.conf import settings
from deep_translator import GoogleTranslator

from articles.categorizer import categorize

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Redis
# --------------------------------------------------------------------
REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)

REDIS_KEY_PREFIX = "pzn:rss:"
REDIS_TTL = 60 * 60                    # 10 min — how long a rendered feed page stays "fresh"
TRANSLATION_TTL = 60 * 60 * 24 * 7  # 1 week — a given headline's translation almost never changes

# --------------------------------------------------------------------
# RSS sources
# --------------------------------------------------------------------
RSS_SOURCES = {
    "all": [
        {"url": "https://www.geo.tv/rss/1", "name": "جیو نیوز"},
        {"url": "https://arynews.tv/feed/", "name": "اے آر وائی نیوز"},
        {"url": "https://dunyanews.tv/rss.php", "name": "دنیا نیوز"},
    ],
    "pakistan": [
        {"url": "https://www.geo.tv/rss/1", "name": "جیو نیوز"},
        {"url": "https://dunyanews.tv/rss.php", "name": "دنیا نیوز"},
        {"url": "https://arynews.tv/feed/", "name": "اے آر وائی نیوز"},
    ],
    "politics": [
        {"url": "https://www.geo.tv/rss/2", "name": "جیو نیوز"},
        {"url": "https://arynews.tv/category/pakistan/feed/", "name": "اے آر وائی نیوز"},
        {"url": "https://dunyanews.tv/rss.php?cat=P", "name": "دنیا نیوز"},
    ],
    "sports": [
        {"url": "https://www.geo.tv/rss/6", "name": "جیو سپر"},
        {"url": "https://arynews.tv/category/sports/feed/", "name": "اے آر وائی اسپورٹس"},
        {"url": "https://dunyanews.tv/rss.php?cat=S", "name": "دنیا نیوز"},
    ],
    "business": [
        {"url": "https://www.geo.tv/rss/4", "name": "جیو نیوز"},
        {"url": "https://arynews.tv/category/business/feed/", "name": "اے آر وائی بزنس"},
        {"url": "https://dunyanews.tv/rss.php?cat=B", "name": "دنیا نیوز"},
    ],
    "technology": [
        {"url": "https://feeds.bbci.co.uk/urdu/rss.xml", "name": "BBC Urdu Technology"},
        {"url": "https://www.urdupoint.com/rss/technology.rss", "name": "UrduPoint Technology"},
    ],
    "international": [
        {"url": "https://feeds.bbci.co.uk/urdu/rss.xml", "name": "BBC Urdu International"},
    ],
}

_translator = GoogleTranslator(source="en", target="ur")


def translate_to_urdu(text):
    """Translate an English headline to Urdu.

    Cached in Redis by content hash so the same headline is never sent
    to Google Translate twice, even across categories or refresh cycles.
    This was previously the single biggest source of latency: every
    refresh re-translated every headline from scratch, and a cache-miss
    request in views.py used to do this translation *inline* in the
    HTTP response path.
    """
    if not text:
        return text

    cache_key = f"pzn:tr:{hashlib.md5(text.encode('utf-8')).hexdigest()}"
    cached = _redis.get(cache_key)
    if cached is not None:
        return cached

    try:
        translated = _translator.translate(text)
    except Exception as exc:
        logger.warning("Translation error for '%s...': %s", text[:40], exc)
        return text

    _redis.setex(cache_key, TRANSLATION_TTL, translated)
    return translated


def _extract_image(entry):
    for key in ("media_content", "media_thumbnail"):
        media = entry.get(key, [])
        if media and isinstance(media, list) and media:
            image = media[0].get("url")
            if image:
                return image

    enclosures = entry.get("enclosures", [])
    if enclosures:
        return enclosures[0].get("url")

    return None


def _fetch_one(url, source_name, category_slug):
    import feedparser

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.warning("Feed parse error %s: %s", url, exc)
        return []

    if not feed or not feed.entries:
        return []

    items = []
    for entry in feed.entries[:15]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        description = entry.get("summary", "").strip()

        if not title or not link:
            continue

        title_ur = translate_to_urdu(title)
        detected = categorize(title_ur, description, category_slug)

        items.append({
            "title": title_ur,
            "original_title": title,
            "link": link,
            "description": description[:250],
            "image": _extract_image(entry),
            "pubDate": entry.get("published", ""),
            "source": source_name,
            "category": detected,
        })

    return items


def _dedupe_and_filter(all_items, category):
    all_items.sort(key=lambda x: x.get("pubDate", ""), reverse=True)

    seen = set()
    unique = []
    for item in all_items:
        key = item["title"][:60]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    if category != "all":
        filtered = [i for i in unique if i["category"] == category]
        unique = filtered if len(filtered) >= 3 else unique

    return unique


@shared_task(name="backend.articles.tasks.refresh_rss_category")
def refresh_rss_category(category="all"):
    """
    Celery task — fetches RSS feeds for a category, translates + runs
    NLP categorization, stores the result in Redis.

    This must be the ONLY place feeds get fetched/translated. Never call
    _fetch_one or translate_to_urdu synchronously from a Django view —
    that blocks the HTTP response on outbound network calls (feed fetch
    + Google Translate) that can easily take several seconds.
    """
    sources = RSS_SOURCES.get(category, RSS_SOURCES["all"])

    all_items = []
    with ThreadPoolExecutor(max_workers=max(len(sources), 1)) as executor:
        futures = [
            executor.submit(_fetch_one, s["url"], s["name"], category)
            for s in sources
        ]
        for f in as_completed(futures):
            try:
                all_items.extend(f.result())
            except Exception as exc:
                logger.warning("RSS fetch failed: %s", exc)

    unique = _dedupe_and_filter(all_items, category)

    redis_key = f"{REDIS_KEY_PREFIX}{category}"
    if unique:
        _redis.setex(
            redis_key,
            REDIS_TTL,
            json.dumps(unique, ensure_ascii=False),
        )
    else:
        logger.warning("RSS failed for %s, keeping old cache", category)

    logger.info("RSS refreshed: %s — %d items", category, len(unique))
    return len(unique)


@shared_task(name="articles.tasks.refresh_all_categories")
def refresh_all_categories():
    """
    Trigger a refresh for every category at once.

    Wire this into Celery Beat (e.g. every 8 minutes, just under
    REDIS_TTL) so the cache is repopulated *before* it expires. That
    way a real user request almost never hits a cold cache, and
    rss_feed() in views.py never needs to fetch/translate anything
    itself.

    Example beat schedule (settings.py):

        CELERY_BEAT_SCHEDULE = {
            "refresh-all-rss": {
                "task": "articles.tasks.refresh_all_categories",
                "schedule": 480.0,  # seconds
            },
        }
    """
    categories = list(RSS_SOURCES.keys())
    for cat in categories:
        refresh_rss_category.delay(cat)
    return f"Triggered refresh for {len(categories)} categories"