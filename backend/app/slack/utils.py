from typing import Optional

from fastapi import HTTPException
from slack_sdk.web.async_client import AsyncWebClient

from ..core.settings import SLACK_TEAM_ID
from .store import installation_store


async def get_client(
    team_id: Optional[str] = SLACK_TEAM_ID,
    enterprise_id: Optional[str] = None,
    is_enterprise_install: Optional[bool] = False,
):
    bot = await installation_store.async_find_bot(
        # The workspace's ID
        team_id=team_id,
        # in the case where this app gets a request from an Enterprise Grid workspace
        enterprise_id=enterprise_id,
        is_enterprise_install=is_enterprise_install,
    )

    if not (bot_token := bot.bot_token if bot else None):
        # The app may be uninstalled or be used in a shared channel
        raise HTTPException(status_code=403, detail="Please install this app first!")

    return AsyncWebClient(token=bot_token)
