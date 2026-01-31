import redis
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI, Request

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


@app.get("/users")
async def users(request: Request):
    db_pool = request.app.state.db_pool
    async with db_pool.acquire() as connection:
        result = await connection.fetch("SELECT name FROM users")
        return result
