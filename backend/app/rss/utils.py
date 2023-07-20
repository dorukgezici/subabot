from feedparser import parse

from ..db import db_feeds
from ..helpers import now_timestamp
from ..models import Feed


def run_crawler(feed: Feed) -> None:
    d = parse(feed.url)
    print(d.feed)

    feed['refreshed_at'] = now_timestamp()
    db_feeds.put(feed.model_dump(), feed.key)
