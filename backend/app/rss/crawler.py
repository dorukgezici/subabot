from typing import Any, AsyncGenerator, Dict, Generator, List, Tuple, Union

from asyncer import asyncify
from fastapi.logger import logger
from feedparser import FeedParserDict, parse

from ..core import db_feeds, db_history, db_keywords, now_timestamp
from ..core.utils import fetch_all
from .models import Feed, History, Keyword

Path = Tuple[str, ...]
Entry = Dict[str, Any]


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

    async with db_history as db:
        links = [history.get("link") for history in await fetch_all(db)]

    indexes = set(int(match[0]) for match in matches)
    return [entries[i] for i in indexes if entries[i].get("link") not in links]


async def crawl_feed(feed: Feed, keywords: List[Keyword]) -> List[Entry]:
    """Runs the crawler for the given feed and keywords."""

    data: FeedParserDict = await asyncify(parse)(feed.url)
    matches: Dict[str, List[Path]] = {}

    async with db_feeds as db:
        new_feed = feed.model_dump()
        new_feed.update(
            {
                "refreshed_at": now_timestamp(),
                "data": {
                    "feed": data.feed,
                    "entries": data.entries,
                },
            },
        )
        await db.put(new_feed, feed.key)

    async with db_keywords as db:
        for keyword in keywords:
            matches[feed.key] = [match for match in find_matches(list(data.entries), keyword.value)]

            # this reload was needed not to overwrite the matches from other feeds
            if not isinstance(new_keyword := await db.get(keyword.key), dict):
                new_keyword = keyword.model_dump()

            new_keyword["checked_at"] = now_timestamp()
            new_keyword["matches"][feed.key] = matches[feed.key]
            await db.put(new_keyword, keyword.key)

    entries = await get_matching_entries(data.entries, matches[feed.key])
    logger.debug(f"Found {len(entries)} new entries for {feed.url}.")

    if len(entries) > 0:
        async with db_history as db:
            history = [History(link=entry["link"], created_at=now_timestamp()) for entry in entries]
            # keep history for 2 days via `expire_in`
            await db.put_many([h.model_dump() for h in history], expire_in=172800)

    return entries


async def run_crawler() -> AsyncGenerator[List[Entry], Any]:
    """Runs the crawler for all feeds and keywords."""

    # Query feeds that were refreshed more than a minute ago or never at all
    async with db_feeds as db:
        res = await db.fetch([{"refreshed_at?lt": now_timestamp() - 60}, {"refreshed_at": None}])
        feeds = [Feed(**feed) for feed in res.items]

    async with db_keywords as db:
        res = await db.fetch()
        keywords = [Keyword(**keyword) for keyword in res.items]

    logger.debug(f"Crawling {len(feeds)} feeds for {len(keywords)} keywords...")

    for feed in feeds:
        yield await crawl_feed(feed, keywords)
