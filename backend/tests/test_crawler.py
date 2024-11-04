import pytest
from prefect.logging.loggers import disable_run_logger
from sqlmodel import SQLModel, select

from subabot.db import Session, engine
from subabot.rss.crawler import crawl_feed, run_crawler
from subabot.rss.models import Feed, Keyword
from subabot.utils import now_timestamp

SQLModel.metadata.create_all(engine)


@pytest.mark.asyncio
async def test_crawl_feed() -> None:
    with disable_run_logger():
        feed = Feed(key="https://www.haberturk.com/rss", title="Haberturk")
        keyword = Keyword(key="haber", value="haber", checked_at=now_timestamp())

        with Session(engine) as session:
            feed = session.exec(select(Feed).where(Feed.key == feed.key)).first() or feed
            keyword = session.exec(select(Keyword).where(Keyword.key == keyword.key)).first() or keyword

        await crawl_feed.fn(feed=feed, keywords=[keyword])


@pytest.mark.asyncio
async def test_run_crawler() -> None:
    with disable_run_logger():
        await run_crawler.fn()
