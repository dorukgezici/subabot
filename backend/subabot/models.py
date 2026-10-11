from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import JSON, Column, Field, SQLModel


def now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid4().hex


class Workspace(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str = "My workspace"
    token_hash: str = Field(unique=True, index=True)
    webhook_url: str | None = None
    created_at: datetime = Field(default_factory=now)


class Monitor(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    name: str
    description: str = ""
    keywords: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    exclude_keywords: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    match_mode: str = "any"
    feed_urls: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    enabled: bool = True
    color: str = "#357a57"
    public: bool = False
    share_slug: str | None = Field(default=None, unique=True, index=True)
    created_at: datetime = Field(default_factory=now)
    last_checked_at: datetime | None = None
    last_error: str | None = None


class Signal(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("monitor_id", "fingerprint", name="unique_monitor_article"),)

    id: str = Field(default_factory=new_id, primary_key=True)
    workspace_id: str = Field(foreign_key="workspace.id", index=True)
    monitor_id: str = Field(foreign_key="monitor.id", index=True)
    fingerprint: str
    title: str
    url: str
    summary: str = ""
    source: str
    published_at: datetime = Field(default_factory=now)
    matched_keywords: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    is_read: bool = False
    is_bookmarked: bool = False
    created_at: datetime = Field(default_factory=now)
    delivery_pending: bool = False
    delivered_at: datetime | None = None
