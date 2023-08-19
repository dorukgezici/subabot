from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from fastapi.logger import logger
from starlette.status import HTTP_200_OK

from ..core import db_feeds, db_keywords, fetch_all
from ..rss import FEEDS, KEYWORDS, Feed, Keyword
from .blocks import generate_configuration_blocks
from .dependencies import CommandForm
from .utils import crawl_and_alert

router = APIRouter()


@router.post("/configure")
async def handle_cmd_configure(command: Annotated[CommandForm, Depends()]):
    async with db_feeds as db_f, db_keywords as db_k:
        feeds = [Feed(**feed) for feed in await fetch_all(db_f)]
        keywords = [Keyword(**keyword) for keyword in await fetch_all(db_k)]

    return {
        "response_type": "ephemeral",
        "text": "Configure Subabot",
        "blocks": generate_configuration_blocks(
            feeds=feeds,
            keywords=keywords,
            channel=command.channel_id,
        ),
    }


@router.post("/crawl")
async def handle_cmd_crawl(background_tasks: BackgroundTasks):
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
