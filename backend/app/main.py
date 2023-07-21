import logging

from fastapi import FastAPI
from fastapi.logger import logger

from .db import db_events, db_feeds, db_keywords
from .helpers import now_timestamp
from .models import Action, Feed
from .rss import feeds, keywords, run_crawler

uvicorn_logger = logging.getLogger('uvicorn')
logger.handlers = uvicorn_logger.handlers
logger.setLevel(uvicorn_logger.level)

app = FastAPI(title='Subabot', version='0.1.0')


@app.on_event('startup')
async def on_startup():
    logger.info("Loading initial RSS feeds and keywords to the db...")
    db_feeds.put_many([feed.model_dump() for feed in feeds])
    db_keywords.put_many([keyword.model_dump() for keyword in keywords])


@app.get('/')
async def health():
    return {'status': 'ok'}


# Deta Space: Scheduled Actions
@app.post('/__space/v0/actions')
def actions(action: Action) -> None:
    event = action.event.model_dump()
    event['created_at'] = now = now_timestamp()
    db_events.put(event)

    # Crawl feeds that were last refreshed more than 4 minutes ago
    for feed in db_feeds.fetch([{'refreshed_at?lt': now - 240}, {'refreshed_at': None}]).items:
        run_crawler(Feed(**feed))
