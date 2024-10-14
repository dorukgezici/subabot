from typing import Any, Dict, Optional, Self

from pydantic import model_validator
from slugify import slugify
from sqlmodel import JSON, Column, Field, SQLModel

from subabot.db import DBMixin
from subabot.utils import now_timestamp


class Keyword(SQLModel, DBMixin, table=True):
    key: str = Field(primary_key=True)
    value: str
    checked_at: Optional[int] = Field(default=None)

    @model_validator(mode="before")
    def populate_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["key"] = slugify(values["value"])
        return values


class Feed(SQLModel, DBMixin, table=True):
    key: str = Field(primary_key=True)
    title: str
    refreshed_at: Optional[int] = Field(default=None)

    @model_validator(mode="before")
    def populate_title(cls, obj: Self) -> Self:
        if not obj.title:
            obj.title = obj.key
        return obj


class Crawl(SQLModel, DBMixin, table=True):
    key: str = Field(primary_key=True)
    feed: dict = Field(sa_column=Column(JSON), default_factory=dict)
    entries: list[dict] = Field(sa_column=Column(JSON), default_factory=list)
    updated_at: int = Field(default_factory=now_timestamp)


class Search(SQLModel, DBMixin, table=True):
    key: str = Field(primary_key=True)
    keyword: str
    feed: str
    paths: list[tuple] = Field(sa_column=Column(JSON), default_factory=list)
    updated_at: int = Field(default_factory=now_timestamp)


class History(SQLModel, DBMixin, table=True):
    key: str = Field(primary_key=True)
    updated_at: int = Field(default_factory=now_timestamp)
