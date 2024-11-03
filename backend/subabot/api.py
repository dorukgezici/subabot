from typing import Dict, Literal

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from subabot.config import settings
from subabot.db import engine
from subabot.rss.router import router as rss_router
from subabot.slack.app import app as slack_app

app = FastAPI(title="Subabot", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.subabot_frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rss_router)
app.mount("/slack", slack_app)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/")
async def health() -> Dict[Literal["status"], Literal["ok"]]:
    return {"status": "ok"}


def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)
