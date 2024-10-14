from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from starlette.status import HTTP_200_OK

from subabot.config import APP_DIR
from subabot.db import SessionDep
from subabot.rss.models import Feed, Keyword
from subabot.slack.blocks import generate_configuration_blocks
from subabot.slack.dependencies import CommandForm
from subabot.slack.utils import crawl_and_alert

router = APIRouter()


@router.post("/configure")
async def handle_cmd_configure(command: Annotated[CommandForm, Depends()], session: SessionDep):
    feeds = list(Feed.list())
    keywords = list(Keyword.list())

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
async def handle_cmd_import(session: SessionDep, background_tasks: BackgroundTasks):
    with open(APP_DIR / "rss/feeds/tr.txt") as f:
        urls = [line.strip() for line in f.readlines()]

    for url in urls:
        Feed.upsert(session, key=url, title=url)

    # run crawler in the background
    background_tasks.add_task(crawl_and_alert)

    return Response(status_code=HTTP_200_OK)
