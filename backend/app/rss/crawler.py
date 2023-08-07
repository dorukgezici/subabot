from typing import Any, Dict, Generator, List, Tuple, Union

from asyncer import asyncify
from feedparser import FeedParserDict, parse

from ..core import db_feeds, db_keywords, now_timestamp
from .models import Feed, Keyword


def find_matches(
    data: Union[List[Dict[str, Any]], Dict[str, Any], str],
    keyword: str,
    pre_path: Tuple[str, ...] = (),
) -> Generator[Tuple[str], Any, Any]:
    """Returns a tuple of paths to the keyword found in the data."""

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


def get_matching_entries(entries: List[FeedParserDict], matches: List[Tuple[str, ...]]) -> List[Dict[str, Any]]:
    """Returns a list of unique entries from the matches."""

    indexes = set(match[0] for match in matches)
    return [entries[int(index)] for index in indexes]


async def crawl_feed(feed: Feed, keywords: List[Keyword]) -> List[Dict[str, Any]]:
    """Runs the crawler for the given feed and keywords."""

    data: FeedParserDict = await asyncify(parse)(feed.url)
    matches: Dict[str, List[Tuple[str, ...]]] = {}

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

    return get_matching_entries(data.entries, matches[feed.key])


async def run_crawler():
    """Runs the crawler for all feeds and keywords."""

    # Query feeds that were refreshed more than a minute ago or never at all
    async with db_feeds as db:
        res = await db.fetch([{"refreshed_at?lt": now_timestamp() - 60}, {"refreshed_at": None}])
        feeds = [Feed(**feed) for feed in res.items]

    async with db_keywords as db:
        res = await db.fetch()
        keywords = [Keyword(**keyword) for keyword in res.items]

    for feed in feeds:
        yield await crawl_feed(feed, keywords)
