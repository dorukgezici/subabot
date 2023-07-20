import logging

from fastapi import FastAPI

from .db import db_events, db_feeds, db_keywords
from .helpers import now_timestamp
from .models import Action
from .rss import feeds, keywords, run_crawler

logger = logging.getLogger(__name__)
app = FastAPI(title='Subabot', version='0.1.0')


@app.on_event('startup')
async def on_startup():
    logger.info("Loading initial RSS feeds and keywords to the db...")
    db_feeds.put_many([feed.model_dump() for feed in feeds])
    db_keywords.put_many([keyword.model_dump() for keyword in keywords])


@app.get('/')
async def health():
    return {'status': 'ok'}


# Deta Space Scheduled Actions
@app.post('/__space/v0/actions')
def actions(action: Action) -> None:
    event = action.event.model_dump()
    event['created_at'] = now_timestamp()
    db_events.put(event)

    for feed in feeds:
        run_crawler(feed)
