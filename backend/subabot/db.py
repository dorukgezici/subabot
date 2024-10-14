from dataclasses import dataclass
from typing import Annotated, Self, Sequence

from fastapi import Depends
from sqlmodel import Session, create_engine, select

from subabot.utils import now_timestamp

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@dataclass
class DBMixin:
    """Mixin for SQLModel classes"""

    key: str

    @classmethod
    def get(cls, key: str, session: Session | None = None) -> Self:
        with session or Session(engine) as session:
            if obj := session.exec(select(cls).where(cls.key == key)).first():
                return obj

            raise ValueError(f"{cls.__name__} with key '{key}' not found.")

    @classmethod
    def delete(cls, key: str, session: Session | None = None) -> None:
        with session or Session(engine) as session:
            if obj := session.exec(select(cls).where(cls.key == key)).first():
                session.delete(obj)
                session.commit()
                return

            raise ValueError(f"{cls.__name__} with key '{key}' not found.")

    @classmethod
    def list(cls, session: Session | None = None) -> Sequence[Self]:
        with session or Session(engine) as session:
            return session.exec(select(cls)).all()

    @classmethod
    def upsert(cls, session: Session | None = None, **fields) -> Self:
        with session or Session(engine) as session:
            if obj := session.exec(select(cls).where(cls.key == fields.get("key"))).first():
                for field_key, value in fields.items():
                    setattr(obj, field_key, value)
            else:
                obj = cls(**fields)

            if "updated_at" in getattr(cls, "model_fields"):
                setattr(obj, "updated_at", now_timestamp())

            session.add(obj)
            session.commit()
            return obj


__all__ = ["engine", "Session", "SessionDep", "DBMixin"]
