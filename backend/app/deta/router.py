from fastapi import APIRouter

from ..core import db_events, db_feeds, db_keywords, now_timestamp
from ..core.settings import SLACK_CHANNEL_ID
from ..rss import Feed, Keyword, run_crawler
from ..slack import get_client
from .models import Action

router = APIRouter(prefix="/__space")


@router.post("/v0/actions")
async def actions(action: Action) -> None:
    event = action.event.model_dump()
    event["created_at"] = now = now_timestamp()
    db_events.put(event)

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
