from typing import Optional

from pydantic import BaseModel, Field


class Feed(BaseModel):
    key: str
    title: str
    url: str

    refreshed_at: Optional[int] = Field(default=None)
    rss: Optional[dict] = Field(default=None)


class Keyword(BaseModel):
    key: str
    value: str

    checked_at: Optional[int] = Field(default=None)


# Deta Space: Scheduled Actions
class Event(BaseModel):
    id: str
    trigger: str


class Action(BaseModel):
    event: Event
