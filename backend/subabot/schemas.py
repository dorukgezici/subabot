from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from subabot.safety import safe_url, safe_webhook


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class WorkspaceInput(InputModel):
    name: str = Field(default="My workspace", min_length=1, max_length=80)


class MonitorInput(InputModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=300)
    keywords: list[str] = Field(min_length=1, max_length=20)
    exclude_keywords: list[str] = Field(default_factory=list, max_length=20)
    match_mode: Literal["any", "all"] = "any"
    feed_urls: list[str] = Field(min_length=1, max_length=10)
    enabled: bool = True
    color: str = Field(default="#357a57", pattern=r"^#[0-9a-fA-F]{6}$")
    public: bool = False

    @field_validator("keywords", "exclude_keywords")
    @classmethod
    def validate_keywords(cls, values):
        result = list(dict.fromkeys(value.strip().lower() for value in values))
        if any(not value or len(value) > 80 for value in result):
            raise ValueError("Keywords must contain between 1 and 80 characters.")
        return result

    @field_validator("feed_urls")
    @classmethod
    def validate_feeds(cls, values):
        return list(dict.fromkeys(safe_url(value.strip()) for value in values))


class MonitorPatch(InputModel):
    name: str | None = None
    description: str | None = None
    keywords: list[str] | None = None
    exclude_keywords: list[str] | None = None
    match_mode: Literal["any", "all"] | None = None
    feed_urls: list[str] | None = None
    enabled: bool | None = None
    color: str | None = None
    public: bool | None = None


class MonitorView(MonitorInput):
    model_config = ConfigDict(from_attributes=True)
    id: str
    share_slug: str | None
    created_at: datetime
    last_checked_at: datetime | None
    last_error: str | None


class SignalPatch(InputModel):
    is_read: bool | None = None
    is_bookmarked: bool | None = None


class SignalView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    monitor_id: str
    title: str
    url: str
    summary: str
    source: str
    published_at: datetime
    matched_keywords: list[str]
    is_read: bool
    is_bookmarked: bool


class SlackInput(InputModel):
    webhook_url: str = Field(max_length=500)

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, value):
        return safe_webhook(value)


class TemplateInput(InputModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
