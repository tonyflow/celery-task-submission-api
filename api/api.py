from contextlib import asynccontextmanager

import asyncpg
import redis
from celery import Celery
from fastapi import FastAPI, Query
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from models import UserResponse

cache = redis.Redis(host="redis", port=6379)
celery_app = Celery("worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://redis:6379/0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up")
    app.state.db_pool = await asyncpg.create_pool(
        user="postgres",
        password="postgres",
        database="postgres",
        host="postgres",
        port=5432,
        min_size=1,
        max_size=10,
    )

    yield

    await app.state.db_pool.close()
    print("Shutdown complete")


app = FastAPI(
    lifespan=lifespan,
)


def get_hit_count():
    return cache.incr("hits")


@app.get("/hit")
def hello():
    count = get_hit_count()
    return "Hello World! I have been seen {} times.".format(count)


@app.get("/users",response_model=list[UserResponse])
async def users():
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


@app.post("/task")
def create_task(x: int = Query(...), y: int = Query(...)):
    task = celery_app.send_task("worker.add", args=[x, y])
    return {"task_id": task.id}


@app.get("/poll")
def poll_task(task_id: str = Query(...)):
    result = celery_app.AsyncResult(task_id)
    response = {"task_id": task_id, "state": result.state}
    if result.ready():
        response["result"] = result.result
    return response
