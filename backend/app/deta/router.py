from fastapi import APIRouter

from ..core import db_events, db_feeds, db_keywords, now_timestamp
from ..rss import Feed, Keyword, run_crawler
from ..slack import get_client, installation_store
from .models import Action

router = APIRouter(prefix="/__space")


@router.post("/v0/actions")
async def actions(action: Action) -> None:
    event = action.event.model_dump()
    event["created_at"] = now = now_timestamp()
    db_events.put(event)

    # Query feeds that were refreshed more than 4 minutes ago or never at all
    feeds = [Feed(**feed) for feed in db_feeds.fetch([{"refreshed_at?lt": now - 240}, {"refreshed_at": None}]).items]
    keywords = [Keyword(**keyword) for keyword in db_keywords.fetch().items]

    # Slack client
    client = await get_client(installation_store=installation_store, team_id="T05H4RS4UG5")

    for feed in feeds:
        matches = run_crawler(feed, keywords)

        await client.chat_postMessage(
            channel="C05HA7AU7EG",
            text=f"Feed <{feed.url}|{feed.title}> refreshed.",
        )
