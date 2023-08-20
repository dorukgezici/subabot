from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, HttpUrl, field_serializer, model_validator
from slugify import slugify

Path = Tuple[str, ...]
Entry = Dict[str, Any]


class Keyword(BaseModel):
    value: str
    key: str
    checked_at: Optional[int] = Field(default=None)

    @classmethod
    def create(cls, value: str) -> "Keyword":
        return cls(value=value, key=slugify(value))

    @model_validator(mode="before")
    def populate_key(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "key" not in values:
            values["key"] = slugify(values["value"])

        return values


class Feed(BaseModel):
    key: HttpUrl
    title: str
    refreshed_at: Optional[int] = Field(default=None)

    @classmethod
    def create(cls, url: str) -> "Feed":
        http_url = HttpUrl(url=url)
        return cls(key=http_url, title=http_url.unicode_host() or url)

    @model_validator(mode="before")
    def populate_title(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        url = values["key"]
        http_url = HttpUrl(url=url)

        if "title" not in values:
            values["title"] = http_url.unicode_host() or url

        return values

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return str(key)


class Crawl(BaseModel):
    key: HttpUrl
    feed: dict
    entries: List[Entry]
    updated_at: int

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return str(key)


class Search(BaseModel):
    key: Optional[str] = Field(default=None)
    keyword: str
    feed: HttpUrl
    paths: List[Path]
    updated_at: int

    @field_serializer("feed")
    def serialize_feed(self, feed: HttpUrl, _info):
        return str(feed)


class History(BaseModel):
    key: HttpUrl
    updated_at: int

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return str(key)
