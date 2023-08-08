import os
from typing import List

from fastapi import FastAPI
from fastapi.logger import logger

from .core import db_feeds, db_keywords, fetch_all
from .deta import router as deta_router
from .rss import FEEDS, KEYWORDS
from .slack import app as slack_app

app = FastAPI(
    title="Subabot",
    version="0.1.0",
    # needed for Deta Space `/docs` to work
    root_path="/api" if "DETA_SPACE_APP_HOSTNAME" in os.environ else "",
)
app.include_router(deta_router)
app.mount("/slack", slack_app)


@app.on_event("startup")
async def on_startup():
    async with db_feeds as db:
        if len(await fetch_all(db)) == 0:
            logger.info("Loading initial RSS feeds to the db...")
            await db.put_many([feed.model_dump() for feed in FEEDS])

    async with db_keywords as db:
        if len(await fetch_all(db)) == 0:
            logger.info("Loading initial keywords to the db...")
            await db.put_many([keyword.model_dump() for keyword in KEYWORDS])


@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/feeds")
async def read_feeds() -> List[dict]:
    async with db_feeds as db:
        feeds = await fetch_all(db)

    return feeds


@app.get("/keywords")
async def read_keywords() -> List[dict]:
    async with db_keywords as db:
        keywords = await fetch_all(db)

    return keywords
