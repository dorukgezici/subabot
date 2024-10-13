from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

engine = create_engine("sqlite:///database.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

__all__ = ["SessionDep"]
