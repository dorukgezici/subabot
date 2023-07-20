from pydantic import BaseModel


class Feed(BaseModel):
    key: str
    title: str
    url: str


class Keyword(BaseModel):
    key: str
    value: str


# Deta Space
class Event(BaseModel):
    id: str
    trigger: str


class Action(BaseModel):
    event: Event
