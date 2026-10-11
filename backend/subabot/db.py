from pathlib import Path

from sqlalchemy import event
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool


def make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def configure_sqlite(connection, _):
            if engine.url.database not in {None, "", ":memory:"}:
                # Slack webhooks are secrets. New local databases must not be world-readable.
                Path(engine.url.database).chmod(0o600)
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=30000")

    return engine
