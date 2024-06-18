from pydantic import BaseModel


class Event(BaseModel):
    id: str
    trigger: str


class Action(BaseModel):
    event: Event
