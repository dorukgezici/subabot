import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import db_feeds, db_keywords, fetch_all
from .deta import router as deta_router
from .slack import app as slack_app

app = FastAPI(
    title="Subabot",
    version="0.1.0",
    # needed for Deta Space `/docs` to work
    root_path="/api" if "DETA_SPACE_APP_HOSTNAME" in os.environ else "",
)
app.include_router(deta_router)
app.mount("/slack", slack_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health():
    return {"status": "ok"}


@app.get("/feeds")
async def read_feeds() -> List[dict]:
    async with db_feeds as db:
        feeds = await fetch_all(db)

    return feeds


@app.get("/keywords")
async def read_keywords() -> List[dict]:
    async with db_keywords as db:
        keywords = await fetch_all(db)

    return keywords
