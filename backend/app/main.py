import logging
import os
from typing import List

from fastapi import FastAPI
from fastapi.logger import logger

from .core import db_feeds, db_keywords, fetch_all
from .deta import router as deta_router
from .rss import feeds, keywords
from .slack import app as slack_app

uvicorn_logger = logging.getLogger("uvicorn")
logger.handlers = uvicorn_logger.handlers
logger.setLevel(uvicorn_logger.level)

app = FastAPI(
    title="Subabot",
    version="0.1.0",
    # needed for 'space dev' docs to work
    root_path="/api" if "DETA_SPACE_APP_HOSTNAME" in os.environ else "",
)
app.include_router(deta_router)
app.mount("/slack", slack_app)


@app.on_event("startup")
def on_startup():
    if len(fetch_all(db_feeds)) == 0:
        logger.info("Loading initial RSS feeds to the db...")
        db_feeds.put_many([feed.model_dump() for feed in feeds])

    if len(fetch_all(db_keywords)) == 0:
        logger.info("Loading initial keywords to the db...")
        db_keywords.put_many([keyword.model_dump() for keyword in keywords])


@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/feeds")
def read_feeds() -> List[dict]:
    return fetch_all(db_feeds)


@app.get("/keywords")
def read_keywords() -> List[dict]:
    return fetch_all(db_keywords)
