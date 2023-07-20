from sqlmodel import Field, SQLModel


class Event(SQLModel):
    id: str = Field(default=None, primary_key=True)
    trigger: str


class Action(SQLModel):
    event: Event
