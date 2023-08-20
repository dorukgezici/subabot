from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, HttpUrl, field_serializer, field_validator

Path = Tuple[str, ...]
Entry = Dict[str, Any]


class Keyword(BaseModel):
    key: str
    value: str

    checked_at: Optional[int] = Field(default=None)


class Feed(BaseModel):
    key: HttpUrl
    title: str

    refreshed_at: Optional[int] = Field(default=None)

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return key.unicode_string()


class Crawl(BaseModel):
    key: HttpUrl
    feed: dict
    entries: List[Entry]
    updated_at: int

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return key.unicode_string()


class Search(BaseModel):
    key: Optional[str] = Field(default=None)
    keyword: str
    feed: HttpUrl
    paths: List[Path]
    updated_at: int

    @field_serializer("feed")
    def serialize_feed(self, feed: HttpUrl, _info):
        return feed.unicode_string()


class History(BaseModel):
    key: HttpUrl
    updated_at: int

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return key.unicode_string()
