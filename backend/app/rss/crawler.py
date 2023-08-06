from typing import Any, Dict, Generator, List, Tuple, Union

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


def run_crawler(feed: Feed, keywords: List[Keyword]) -> List[Dict[str, Any]]:
    """Runs the crawler for the given feed and keywords."""
    data: FeedParserDict = parse(feed.url)

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
    db_feeds.put(new_feed, feed.key)

    matches: Dict[str, List[Tuple[str, ...]]] = {}
    for keyword in keywords:
        matches[feed.key] = [match for match in find_matches(list(data.entries), keyword.value)]

        # this reload was needed not to overwrite the matches from other feeds
        if not isinstance(new_keyword := db_keywords.get(keyword.key), dict):
            new_keyword = keyword.model_dump()

        new_keyword["checked_at"] = now_timestamp()
        new_keyword["matches"][feed.key] = matches[feed.key]
        db_keywords.put(new_keyword, keyword.key)

    return get_matching_entries(data.entries, matches[feed.key])
