import os
from typing import Dict, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from subabot.core.settings import FRONTEND_URL
from subabot.rss.router import router as rss_router
from subabot.slack.app import app as slack_app

app = FastAPI(
    title="Subabot",
    version="0.1.0",
    # needed for Deta Space `/api/docs` to work
    root_path="/api" if "DETA_SPACE_APP_HOSTNAME" in os.environ else "",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rss_router)
app.mount("/slack", slack_app)


@app.get("/")
async def health() -> Dict[Literal["status"], Literal["ok"]]:
    return {"status": "ok"}
