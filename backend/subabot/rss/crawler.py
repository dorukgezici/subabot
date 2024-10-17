import asyncio
from typing import Sequence

from asyncer import asyncify
from fastapi.logger import logger
from feedparser import FeedParserDict, parse
from prefect import task
from sqlmodel import select

from subabot.db import Session, engine
from subabot.rss.models import Crawl, Feed, History, Keyword, Search
from subabot.rss.utils import find_matches, get_matching_entries
from subabot.utils import now_timestamp


@task
async def crawl_feed(feed: Feed, keywords: Sequence[Keyword]) -> Sequence[dict]:
    """Runs the crawler for the given feed and keywords."""

    url = feed.key
    data = FeedParserDict(await asyncify(parse)(url))  # type: ignore
    feed_info, entries = data.feed, data.entries
    assert isinstance(feed_info, dict)
    assert isinstance(entries, list)

    with Session(engine) as session:
        Crawl.upsert(session, key=url, feed=feed_info, entries=entries)
        Feed.upsert(session, key=url, title=feed_info.get("title", feed.title), refreshed_at=now_timestamp())

        matches: list[tuple] = []
        for keyword in keywords:
            Keyword.upsert(session, key=keyword.key, value=keyword.value, checked_at=now_timestamp())
            keyword_matches = [path for path in find_matches(entries, keyword.value)]
            matches.extend(keyword_matches)
            Search.upsert(
                session,
                key=keyword.key,
                keyword=keyword.value,
                feed=feed.key,
                paths=keyword_matches,
            )

        entries = get_matching_entries(entries, matches)
        logger.debug(f"Found {len(entries)} new entries for {url}.")

        for entry in entries:
            if link := entry.get("link"):
                History.upsert(session, key=link)

    return entries


@task
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
    results = await asyncio.gather(*crawlers, return_exceptions=True)  # type: ignore
    return [entry for result in results if isinstance(result, list) for entry in result]
