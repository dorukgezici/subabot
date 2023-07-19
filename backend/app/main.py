from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from .db import get_session, init_db
from .models import Task, TaskCreate

app = FastAPI(title="subabot", version="0.1.0")


@app.on_event("startup")
async def on_startup():
    await init_db()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/tasks", response_model=list[Task])
async def read_tasks(session: AsyncSession = Depends(get_session)):
    tasks = await session.execute(select(Task))
    return tasks.scalars().all()


@app.post("/task/", response_model=Task)
async def create_task(task: TaskCreate, session: AsyncSession = Depends(get_session)):
    task = Task(task_name=task.task_name)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task
