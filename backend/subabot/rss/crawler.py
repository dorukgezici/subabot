import asyncio
from typing import Sequence

from asyncer import asyncify
from fastapi.logger import logger
from feedparser import FeedParserDict, parse

from sqlmodel import select

from subabot.db import Session, engine
from subabot.rss.models import Crawl, Feed, History, Keyword, Search
from subabot.utils import now_timestamp
from subabot.rss.utils import find_matches, get_matching_entries


async def crawl_feed(feed: Feed, keywords: Sequence[Keyword]) -> list[dict]:
    """Runs the crawler for the given feed and keywords."""

    url = feed.key
    data = FeedParserDict(await asyncify(parse)(url))
    feed_info, entries = data.feed, list(data.entries)
    assert isinstance(feed_info, dict)
    assert isinstance(entries, list)

    Crawl.upsert(url, feed=feed_info, entries=entries)
    Feed.upsert(url, title=feed_info.get("title", feed.title), refreshed_at=now_timestamp())

    matches: list[tuple] = []
    for keyword in keywords:
        Keyword.upsert(keyword.key, value=keyword.value, checked_at=now_timestamp())
        keyword_matches = [path for path in find_matches(entries, keyword.value)]
        matches.extend(keyword_matches)
        Search.upsert(
            keyword.key,
            keyword=keyword.value,
            feed=feed.key,
            paths=keyword_matches,
            updated_at=now_timestamp(),
        )

    entries = get_matching_entries(entries, matches)
    logger.debug(f"Found {len(entries)} new entries for {url}.")

    for entry in entries:
        if link := entry.get("link"):
            History.upsert(link, updated_at=now_timestamp())

    return entries


async def run_crawler() -> list[dict]:
    """Runs the crawler for all feeds and keywords."""

    # Query feeds that were refreshed more than a minute ago or never at all
    with Session(engine) as session:
        # one_minute_ago = (now() - timedelta(minutes=1)).timestamp()
        feeds = session.exec(select(Feed).where((Feed.refreshed_at is None))).all()
        keywords = session.exec(select(Keyword)).all()

    logger.debug(f"Crawling {len(feeds)} feeds for {len(keywords)} keywords...")

    crawlers = [crawl_feed(feed, keywords) for feed in feeds]
    # swallow exceptions to keep the loop running
    results = await asyncio.gather(*crawlers, return_exceptions=True)
    return [entry for result in results if isinstance(result, list) for entry in result]
