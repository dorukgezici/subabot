import asyncio
from typing import Any, Generator, List, Union, cast

from aiohttp import ClientResponseError
from asyncer import asyncify
from fastapi.logger import logger
from feedparser import FeedParserDict, parse
from prefect import flow

from ..core import get_db_crawls, get_db_feeds, get_db_history, get_db_keywords, get_db_searches, now_timestamp
from ..core.utils import fetch_all
from .models import Crawl, Entry, Feed, History, Keyword, Path, Search


def find_matches(
    data: Union[List[Entry], Entry, str],
    keyword: str,
    pre_path: Path = (),
) -> Generator[Path, Any, Any]:
    """Generates tuples of paths to the keyword found in the data."""

    if isinstance(data, list):
        for index, item in enumerate(data):
            path = pre_path + (str(index),)
            yield from find_matches(item, keyword, path)

    elif isinstance(data, dict):
        for key, value in data.items():
            path = pre_path + (key,)
            yield from find_matches(value, keyword, path)

    elif isinstance(data, str) and keyword.casefold() in data.casefold():
        yield pre_path


async def get_matching_entries(entries: List[FeedParserDict], matches: List[Path]) -> List[Entry]:
    """Returns a list of unique entries from the matches that are NOT in history."""

    async with get_db_history() as db:
        links = [history.get("key") for history in await fetch_all(db)]

    indexes = set(int(match[0]) for match in matches)
    return [entries[i] for i in indexes if entries[i].get("link") not in links]


async def crawl_feed(feed: Feed, keywords: List[Keyword]) -> List[Entry]:
    """Runs the crawler for the given feed and keywords."""

    url = str(feed.key)
    data: FeedParserDict = await asyncify(parse)(url)
    rss_channel, now = cast(dict, data.feed), now_timestamp()

    async with get_db_crawls() as db:
        crawl = Crawl(
            key=feed.key,
            feed=data.feed if isinstance(data.feed, dict) else {},
            entries=list(data.entries),
            updated_at=now,
        )

        try:
            await db.put(crawl.model_dump(mode="json"), url)
        except ClientResponseError as e:
            logger.error(f"Error while saving crawl {url}: {e}")
        else:
            logger.debug(f"Saved crawl for {url}.")

    async with get_db_feeds() as db:
        new_feed = feed.model_dump(mode="json")
        new_feed.update(
            {
                "title": rss_channel.get("title", feed.title),
                "refreshed_at": now,
            },
        )

        try:
            await db.put(new_feed, url)
        except ClientResponseError as e:
            logger.error(f"Error while saving feed {url}: {e}")

    async with get_db_keywords() as db_k, get_db_searches() as db_s:
        new_keywords: List[dict] = []
        matches: List[Path] = []
        searches: List[Search] = []

        for keyword in keywords:
            new_keyword: dict = keyword.model_dump()
            new_keyword["checked_at"] = now_timestamp()
            new_keywords.append(new_keyword)

            keyword_matches = [path for path in find_matches(list(data.entries), keyword.value)]
            matches.extend(keyword_matches)
            searches.append(
                Search(
                    keyword=keyword.key,
                    feed=feed.key,
                    paths=keyword_matches,
                    updated_at=now,
                ),
            )

        await db_k.put_many(list(new_keywords))
        await db_s.put_many([s.model_dump(mode="json") for s in searches])

    entries = await get_matching_entries(data.entries, matches)
    logger.debug(f"Found {len(entries)} new entries for {url}.")

    if len(entries) > 0:
        async with get_db_history() as db:
            history = [History(key=entry["link"], updated_at=now) for entry in entries]
            # keep history for 2 days via `expire_in`
            await db.put_many([h.model_dump(mode="json") for h in history], expire_in=172800)

    return entries


@flow(log_prints=True)
async def run_crawler() -> List[Entry]:
    """Runs the crawler for all feeds and keywords."""

    # Query feeds that were refreshed more than a minute ago or never at all
    async with get_db_feeds() as db:
        res = await db.fetch([{"refreshed_at?lt": now_timestamp() - 60}, {"refreshed_at": None}])
        feeds = [Feed(**feed) for feed in res.items]

    async with get_db_keywords() as db:
        res = await db.fetch()
        keywords = [Keyword(**keyword) for keyword in res.items]

    logger.debug(f"Crawling {len(feeds)} feeds for {len(keywords)} keywords...")

    crawlers = [crawl_feed(feed, keywords) for feed in feeds]
    # swallow exceptions to keep the loop running
    results = await asyncio.gather(*crawlers, return_exceptions=True)
    return [entry for result in results if isinstance(result, list) for entry in result]
