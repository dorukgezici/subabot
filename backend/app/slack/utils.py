from fastapi import HTTPException
from slack_sdk.web.async_client import AsyncWebClient

from .store import DetaDriveInstallationStore


async def get_client(
    installation_store: DetaDriveInstallationStore,
    enterprise_id: str | None = None,
    team_id: str | None = None,
):
    bot = await installation_store.async_find_bot(
        # in the case where this app gets a request from an Enterprise Grid workspace
        enterprise_id=enterprise_id,
        # The workspace's ID
        team_id=team_id,
    )

    if not (bot_token := bot.bot_token if bot else None):
        # The app may be uninstalled or be used in a shared channel
        raise HTTPException(status_code=403, detail="Please install this app first!")

    return AsyncWebClient(token=bot_token)
