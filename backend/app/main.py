from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import fetch_all, get_db_feeds, get_db_keywords
from .core.settings import FRONTEND_URL
from .deta import router as deta_router
from .rss import Feed, Keyword
from .slack import app as slack_app

app = FastAPI(title="Subabot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deta_router)
app.mount("/slack", slack_app)


@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/feeds")
async def read_feeds() -> List[Feed]:
    async with get_db_feeds() as db:
        feeds = [Feed(**data) for data in await fetch_all(db)]

    return feeds


@app.get("/keywords")
async def read_keywords() -> List[Keyword]:
    async with get_db_keywords() as db:
        keywords = [Keyword(**data) for data in await fetch_all(db)]

    return keywords
