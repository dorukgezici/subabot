from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_serializer


class Feed(BaseModel):
    key: HttpUrl
    title: str

    refreshed_at: Optional[int] = Field(default=None)
    data: Optional[dict] = Field(default=None)

    @field_serializer("key")
    def serialize_key(self, key: HttpUrl, _info):
        return key.unicode_string()


class Keyword(BaseModel):
    key: str
    value: str

    checked_at: Optional[int] = Field(default=None)
    matches: dict = Field(default={})


class History(BaseModel):
    key: Optional[str] = Field(default=None)
    link: str
    created_at: int
