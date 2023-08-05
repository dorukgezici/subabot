from typing import Annotated

from asyncer import asyncify
from fastapi import APIRouter, Depends

from ..core import db_feeds, db_keywords, fetch_all
from .dependencies import CommandForm
from .store import installation_store
from .utils import get_client

router = APIRouter()


@router.post("/cmd/configure")
async def handle_cmd_configure(command: Annotated[CommandForm, Depends()]):
    client = await get_client(
        installation_store=installation_store,
        team_id=command.team_id,
        enterprise_id=command.enterprise_id,
    )

    await client.chat_postMessage(
        channel=command.channel_id,
        text="hey",
    )


@router.post("/cmd/keywords")
async def handle_cmd_keywords(command: Annotated[CommandForm, Depends()]):
    keywords = await asyncify(fetch_all)(db=db_keywords)
    return ", ".join(keyword.get("value", "") for keyword in keywords)


@router.post("/cmd/feeds")
async def handle_cmd_feeds(command: Annotated[CommandForm, Depends()]):
    feeds = await asyncify(fetch_all)(db=db_feeds)
    return ", ".join(feed.get("title", "") for feed in feeds)
