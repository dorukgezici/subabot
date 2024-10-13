from fastapi import APIRouter, BackgroundTasks, Body
from fastapi.logger import logger

from subabot.config import APP_DIR
from subabot.db import SessionDep
from sqlmodel import select
from fastapi import HTTPException
from subabot.rss.crawler import crawl_feed
from subabot.rss.models import Feed, Keyword

router = APIRouter()


# Feeds
@router.get("/feeds", response_model=list[Feed])
def read_feeds(session: SessionDep):
    return session.exec(select(Feed)).all()


@router.post("/feeds", response_model=Feed)
def create_feed(feed: Feed, session: SessionDep, background_tasks: BackgroundTasks):
    db_feed = Feed.model_validate(feed)
    session.add(db_feed)
    session.commit()
    session.refresh(db_feed)

    keywords = session.exec(select(Keyword)).all()
    background_tasks.add_task(crawl_feed, feed, keywords)

    return db_feed


@router.delete("/feeds")
def delete_feed(session: SessionDep, body: dict = Body()):
    # had to do a hacky delete since URL can't be read from path
    try:
        url = body["key"]
        feed = session.get(Feed, url)
        if not feed:
            raise HTTPException(status_code=404, detail="Feed not found")
    except KeyError as e:
        logger.warning("Couldn't read key", exc_info=e)
    else:
        session.delete(feed)
        session.commit()


@router.get("/feeds/import", response_model=list[Feed])
def import_feeds(session: SessionDep):
    feeds = []
    with open(APP_DIR / "rss/feeds/tr.txt") as f:
        for line in f.readlines():
            url = line.strip()
            feed = Feed(key=url, title=url)
            feeds.append(feed)
            session.add(feed)

    session.commit()
    session.refresh(feeds)
    return feeds


# Keywords
@router.get("/keywords", response_model=list[Keyword])
def read_keywords(session: SessionDep):
    return session.exec(select(Keyword)).all()


@router.post("/keywords", response_model=Keyword)
def create_keyword(keyword: Keyword, session: SessionDep):
    db_keyword = Keyword.model_validate(keyword)
    session.add(db_keyword)
    session.commit()
    session.refresh(db_keyword)
    return db_keyword


@router.delete("/keywords/{key}")
def delete_keyword(session: SessionDep, key: str):
    keyword = session.get(Keyword, key)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    session.delete(keyword)
    session.commit()
