from typing import Annotated

from asyncer import asyncify
from fastapi import APIRouter, Depends
from slack_sdk.web.async_client import AsyncWebClient

from ..core import db_feeds, db_keywords, fetch_all
from .dependencies import CommandForm, client

router = APIRouter()


@router.post("/configure")
async def handle_cmd_configure(
    client: Annotated[AsyncWebClient, Depends(client)],
    command: Annotated[CommandForm, Depends()],
):
    await client.chat_postMessage(
        channel=command.channel_id,
        text="hey",
    )


@router.post("/keywords")
async def handle_cmd_keywords(command: Annotated[CommandForm, Depends()]):
    keywords = await asyncify(fetch_all)(db=db_keywords)
    return ", ".join(keyword.get("value", "") for keyword in keywords)


@router.post("/feeds")
async def handle_cmd_feeds(command: Annotated[CommandForm, Depends()]):
    feeds = await asyncify(fetch_all)(db=db_feeds)
    return ", ".join(feed.get("title", "") for feed in feeds)
