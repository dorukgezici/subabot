from feedparser import FeedParserDict, parse

from ..db import db_feeds
from ..helpers import now_timestamp
from ..models import Feed


def run_crawler(feed: Feed) -> None:
    d: FeedParserDict = parse(feed.url)

    new_feed = feed.model_dump()
    new_feed.update(
        {
            'refreshed_at': now_timestamp(),
            'rss': {
                'feed': d.feed,
                'entries': d.entries,
            },
        },
    )
    db_feeds.put(new_feed, feed.key)
