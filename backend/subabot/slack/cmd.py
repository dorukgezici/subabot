from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from pydantic import HttpUrl
from starlette.status import HTTP_200_OK

from subabot.core import fetch_all, get_db_feeds, get_db_keywords
from subabot.core.settings import APP_DIR
from subabot.rss import Feed, Keyword
from subabot.slack.blocks import generate_configuration_blocks
from subabot.slack.dependencies import CommandForm
from subabot.slack.utils import crawl_and_alert

router = APIRouter()


@router.post("/configure")
async def handle_cmd_configure(command: Annotated[CommandForm, Depends()]):
    async with get_db_feeds() as db_f, get_db_keywords() as db_k:
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
    # run crawler in the background
    background_tasks.add_task(crawl_and_alert)

    return Response(status_code=HTTP_200_OK)


@router.post("/import")
async def handle_cmd_import(background_tasks: BackgroundTasks):
    with open(APP_DIR / "rss/feeds/tr.txt") as f:
        urls = [line.strip() for line in f.readlines()]

    async with get_db_feeds() as db:
        await db.put_many([Feed(key=HttpUrl(url=url), title=url).model_dump(mode="json") for url in urls])

    # run crawler in the background
    background_tasks.add_task(crawl_and_alert)

    return Response(status_code=HTTP_200_OK)
