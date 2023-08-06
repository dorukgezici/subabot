from typing import Annotated

from asyncer import asyncify
from fastapi import APIRouter, Depends

from ..core import db_feeds, db_keywords, fetch_all
from .dependencies import CommandForm
from .utils import check_and_alert

router = APIRouter()


@router.post("/debug")
async def handle_cmd_debug():
    await check_and_alert()


@router.post("/keywords")
async def handle_cmd_keywords(command: Annotated[CommandForm, Depends()]):
    keywords = await asyncify(fetch_all)(db=db_keywords)
    return ", ".join(keyword.get("value", "") for keyword in keywords)


@router.post("/feeds")
async def handle_cmd_feeds(command: Annotated[CommandForm, Depends()]):
    feeds = await asyncify(fetch_all)(db=db_feeds)
    return ", ".join(feed.get("title", "") for feed in feeds)
