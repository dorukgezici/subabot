from typing import Optional

from fastapi import HTTPException
from slack_sdk.web.async_client import AsyncWebClient

from ..core.settings import SLACK_CHANNEL_ID, SLACK_TEAM_ID
from ..rss import run_crawler
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
        raise HTTPException(status_code=403, detail=f"not authorized for team {team_id}")

    return AsyncWebClient(token=bot_token)


async def crawl_and_alert():
    # Slack client
    client = await get_client()

    async for entries in run_crawler():
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Found <{entry['link']}|{entry['title']}>.",
                },
            }
            for entry in entries
        ]

        if len(blocks) > 0:
            await client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text="New entries found!",
                blocks=blocks,
            )
