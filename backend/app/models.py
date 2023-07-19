from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    task_name: str


class Task(TaskBase, table=True):
    id: int = Field(default=None, primary_key=True)


class TaskCreate(TaskBase):
    pass
