from fastapi import APIRouter, BackgroundTasks

from ..core import get_db_events, now_timestamp
from ..slack import crawl_and_alert
from .models import Action

router = APIRouter(prefix="/__space")


@router.post("/v0/actions")
async def actions(action: Action, background_tasks: BackgroundTasks) -> None:
    async with get_db_events() as db:
        event = action.event.model_dump()
        event["created_at"] = now_timestamp()
        await db.put(event)

    background_tasks.add_task(crawl_and_alert)
