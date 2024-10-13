from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine, select

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@dataclass
class DBMixin:
    key: str

    @classmethod
    def read(cls, key: str):
        with Session(engine) as session:
            if obj := session.exec(select(cls).where(cls.key == key)).first():
                return obj

            raise ValueError(f"{cls.__name__} with key '{key}' not found.")

    @classmethod
    def upsert(cls, key: str, **fields):
        with Session(engine) as session:
            if (obj := session.exec(select(cls).where(cls.key == key)).first()) is None:
                obj = cls(key=key, **fields)
            else:
                for key, value in fields.items():
                    setattr(obj, key, value)

            session.add(obj)
            session.commit()


__all__ = ["engine", "Session", "SessionDep", "DBMixin"]
