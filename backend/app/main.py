import logging
from typing import List

from fastapi import FastAPI
from fastapi.logger import logger

from .db import db_feeds, db_keywords
from .deta import fetch_all
from .deta import router as deta_router
from .rss import feeds, keywords
from .slack import router as slack_router

uvicorn_logger = logging.getLogger("uvicorn")
logger.handlers = uvicorn_logger.handlers
logger.setLevel(uvicorn_logger.level)

app = FastAPI(title="Subabot", version="0.1.0")
app.include_router(deta_router)
app.include_router(slack_router)


@app.on_event("startup")
def on_startup():
    logger.info("Loading initial RSS feeds and keywords to the db...")
    db_feeds.put_many([feed.model_dump() for feed in feeds])
    db_keywords.put_many([keyword.model_dump() for keyword in keywords])


@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/feeds")
def read_feeds() -> List[dict]:
    return fetch_all(db_feeds)
