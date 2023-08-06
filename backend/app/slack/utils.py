from typing import Optional

from fastapi import HTTPException
from slack_sdk.web.async_client import AsyncWebClient

from ..core import db_feeds, db_keywords, now_timestamp
from ..core.settings import SLACK_CHANNEL_ID, SLACK_TEAM_ID
from ..rss import Feed, Keyword, run_crawler
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


async def check_and_alert():
    now = now_timestamp()
    # Query feeds that were refreshed more than a minute ago or never at all
    feeds = [Feed(**feed) for feed in db_feeds.fetch([{"refreshed_at?lt": now - 60}, {"refreshed_at": None}]).items]
    keywords = [Keyword(**keyword) for keyword in db_keywords.fetch().items]

    # Slack client
    client = await get_client()

    for feed in feeds:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Found <{entry['link']}|{entry['title']}> from <{feed.url}|{feed.title}>.",
                },
            }
            for entry in run_crawler(feed, keywords)
        ]

        await client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=f"Feed <{feed.url}|{feed.title}> refreshed.",
            blocks=blocks,
        )
