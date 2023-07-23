from typing import Any, Dict, Generator, List, Tuple, Union

from feedparser import FeedParserDict, parse

from .models import Feed, Keyword
from ..db import db_feeds, db_keywords
from ..helpers import now_timestamp


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


def run_crawler(feed: Feed, keywords: List[Keyword]) -> None:
    data: FeedParserDict = parse(feed.url)

    new_feed = feed.model_dump()
    new_feed.update(
        {
            'refreshed_at': now_timestamp(),
            'data': {
                'feed': data.feed,
                'entries': data.entries,
            },
        },
    )
    db_feeds.put(new_feed, feed.key)

    for keyword in keywords:
        # this reload was needed not to overwrite the matches from other feeds
        new_keyword = db_keywords.get(keyword.key).__dict__
        new_keyword['checked_at'] = now_timestamp()
        new_keyword['matches'][feed.key] = [match for match in find_matches(list(data.entries), keyword.value)]
        db_keywords.put(new_keyword, keyword.key)
