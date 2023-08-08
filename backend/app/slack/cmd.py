from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from starlette.status import HTTP_200_OK

from ..core import db_feeds, db_keywords, fetch_all
from .dependencies import CommandForm
from .utils import configure_blocks, crawl_and_alert

router = APIRouter()


@router.post("/debug")
async def handle_cmd_debug(background_tasks: BackgroundTasks):
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
    async with db_keywords as db:
        keywords = await fetch_all(db)

    return {
        "response_type": "ephemeral",
        "text": "Configure Subabot",
        "blocks": configure_blocks(
            channel=command.channel_id,
            keywords=[keyword["value"] for keyword in keywords],
            unfurls=0,
            notifications=0,
        ),
    }
