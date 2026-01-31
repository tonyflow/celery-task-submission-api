import redis
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI, Request
from database.engine import async_session
from sqlalchemy import select
from database.models import User
from models import UserResponse

cache = redis.Redis(host="redis", port=6379)


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
