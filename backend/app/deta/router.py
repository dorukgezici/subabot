from fastapi import APIRouter

from .models import Action
from ..db import db_events, db_feeds, db_keywords
from ..helpers import now_timestamp
from ..rss import Feed, Keyword, run_crawler

router = APIRouter(prefix='/__space')


@router.post('/v0/actions')
def actions(action: Action) -> None:
    event = action.event.model_dump()
    event['created_at'] = now = now_timestamp()
    db_events.put(event)

    # Query feeds that were refreshed more than 4 minutes ago or never at all
    feeds = [Feed(**feed) for feed in db_feeds.fetch([{'refreshed_at?lt': now - 240}, {'refreshed_at': None}]).items]
    keywords = [Keyword(**keyword) for keyword in db_keywords.fetch().items]

    for feed in feeds:
        run_crawler(feed, keywords)
