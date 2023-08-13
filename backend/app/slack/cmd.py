from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from fastapi.logger import logger
from starlette.status import HTTP_200_OK

from ..core import db_feeds, db_keywords, fetch_all
from ..rss import FEEDS, KEYWORDS, Feed, Keyword
from .dependencies import CommandForm
from .utils import configure_blocks, crawl_and_alert

router = APIRouter()


@router.post("/debug")
async def handle_cmd_debug(background_tasks: BackgroundTasks):
    async with db_feeds as db:
        if len(await fetch_all(db)) == 0:
            logger.info("Loading initial RSS feeds to the db...")
            await db.put_many([feed.model_dump() for feed in FEEDS])

    async with db_keywords as db:
        if len(await fetch_all(db)) == 0:
            logger.info("Loading initial keywords to the db...")
            await db.put_many([keyword.model_dump() for keyword in KEYWORDS])

    # run crawler in the background
    background_tasks.add_task(crawl_and_alert)

    return Response(status_code=HTTP_200_OK)


@router.post("/keywords")
async def handle_cmd_keywords(command: Annotated[CommandForm, Depends()]):
    async with db_keywords as db:
        keywords = await fetch_all(db)

    return {
        "response_type": "ephemeral",
        "text": ", ".join(keyword.get("value", "") for keyword in keywords),
    }


@router.post("/feeds")
async def handle_cmd_feeds(command: Annotated[CommandForm, Depends()]):
    async with db_feeds as db:
        feeds = await fetch_all(db)

    return {
        "response_type": "ephemeral",
        "text": ", ".join(feed.get("title", "") for feed in feeds),
    }


@router.post("/configure")
async def handle_cmd_configure(command: Annotated[CommandForm, Depends()]):
    async with db_feeds as db:
        feeds = [Feed(**feed) for feed in await fetch_all(db)]

    async with db_keywords as db:
        keywords = [Keyword(**keyword) for keyword in await fetch_all(db)]

    return {
        "response_type": "ephemeral",
        "text": "Configure Subabot",
        "blocks": configure_blocks(
            feeds=feeds,
            keywords=keywords,
            channel=command.channel_id,
        ),
    }
