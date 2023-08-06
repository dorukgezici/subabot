from fastapi import APIRouter

from ..core import db_events, now_timestamp
from ..slack.utils import check_and_alert
from .models import Action

router = APIRouter(prefix="/__space")


@router.post("/v0/actions")
async def actions(action: Action) -> None:
    event = action.event.model_dump()
    event["created_at"] = now_timestamp()
    db_events.put(event)

    await check_and_alert()
