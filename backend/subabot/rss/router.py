from typing import List

from fastapi import APIRouter, BackgroundTasks, Body
from fastapi.logger import logger
from pydantic import HttpUrl, ValidationError

from subabot.config import APP_DIR
from subabot.db import SessionDep
from subabot.rss.crawler import crawl_feed
from subabot.rss.models import Feed, Keyword

router = APIRouter()


# Feeds
@router.get("/feeds")
async def read_feeds(session: SessionDep) -> List[Feed]:
    async with get_db_feeds() as db:
        feeds = [Feed(**data) for data in await fetch_all(db)]

    return feeds


@router.post("/feeds")
async def create_feed(feed: Feed, background_tasks: BackgroundTasks) -> Feed:
    async with get_db_feeds() as db:
        await db.put(feed.model_dump(mode="json"))

    async with get_db_keywords() as db:
        keywords = [Keyword(**keyword) for keyword in await fetch_all(db)]
        background_tasks.add_task(crawl_feed, feed, keywords)

    return feed


@router.delete("/feeds")
async def delete_feed(body: dict = Body()) -> None:
    # had to do a hacky delete since URL can't be read from path
    try:
        url = HttpUrl(url=body["key"])
    except (ValidationError, Exception) as e:
        logger.warning(f"Couldn't delete feed: {e}")
    else:
        async with get_db_feeds() as db:
            await db.delete(str(url))


@router.get("/feeds/import")
async def import_feeds() -> List[Feed]:
    with open(APP_DIR / "rss/feeds/tr.txt") as f:
        urls = [line.strip() for line in f.readlines()]

    async with get_db_feeds() as db:
        feeds = [Feed.create(url) for url in urls]
        await db.put_many([f.model_dump(mode="json") for f in feeds])

    return feeds


# Keywords
@router.get("/keywords")
async def read_keywords() -> List[Keyword]:
    async with get_db_keywords() as db:
        keywords = [Keyword(**data) for data in await fetch_all(db)]

    return keywords


@router.post("/keywords")
async def create_keyword(keyword: Keyword) -> Keyword:
    async with get_db_keywords() as db:
        await db.put(keyword.model_dump(mode="json"))

    return keyword


@router.delete("/keywords/{key}")
async def delete_keyword(key: str) -> None:
    async with get_db_keywords() as db:
        await db.delete(key)
