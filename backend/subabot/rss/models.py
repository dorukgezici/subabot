from typing import Any, Dict, Optional

from pydantic import model_validator
from slugify import slugify
from sqlmodel import JSON, Column, Field, SQLModel

# Path = Tuple[str, ...]
Entry = Dict[str, Any]


class Keyword(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
    checked_at: Optional[int] = Field(default=None)

    @model_validator(mode="before")
    def populate_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values["key"] = slugify(values["value"])
        return values


class Feed(SQLModel, table=True):
    key: str = Field(primary_key=True)
    title: str
    refreshed_at: Optional[int] = Field(default=None)

    @model_validator(mode="before")
    def populate_title(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "title" not in values:
            values["title"] = values["key"]
        return values


class Crawl(SQLModel, table=True):
    key: str = Field(primary_key=True)
    feed: dict = Field(sa_column=Column(JSON), default_factory=dict)
    entries: list[dict] = Field(sa_column=Column(JSON), default_factory=list)
    updated_at: int


class Search(SQLModel, table=True):
    key: Optional[str] = Field(default=None, primary_key=True)
    keyword: str
    feed: str
    paths: list[dict] = Field(sa_column=Column(JSON), default_factory=list)
    updated_at: int


class History(SQLModel, table=True):
    key: str = Field(primary_key=True)
    updated_at: int
