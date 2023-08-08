from typing import Optional

from pydantic import BaseModel, Field


class Feed(BaseModel):
    key: str
    title: str
    url: str

    refreshed_at: Optional[int] = Field(default=None)
    data: Optional[dict] = Field(default=None)


class Keyword(BaseModel):
    key: str
    value: str

    checked_at: Optional[int] = Field(default=None)
    matches: dict = Field(default={})


class History(BaseModel):
    key: Optional[str] = Field(default=None)
    link: str
    created_at: int
