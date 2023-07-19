from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_session, init_db
from .models import Task, TaskCreate

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/task/", response_model=Task)
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    task = Task(task_name=task.task_name)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task
