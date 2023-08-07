from fastapi import APIRouter

from ..core import db_events, now_timestamp
from ..slack import crawl_and_alert
from .models import Action

router = APIRouter(prefix="/__space")


@router.post("/v0/actions")
async def actions(action: Action) -> None:
    async with db_events as db:
        event = action.event.model_dump()
        event["created_at"] = now_timestamp()
        await db.put(event)

    await crawl_and_alert()
