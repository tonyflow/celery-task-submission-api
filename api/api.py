import redis
from celery import Celery
from fastapi import FastAPI, Query, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from database.engine import async_session
from database.models import User
from models import UserResponse, TaskResponseBase, TaskResponseState

cache = redis.Redis(host="redis", port=6379)
celery_app = Celery("worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://redis:6379/0")

app = FastAPI()


def get_hit_count():
    return cache.incr("hits")


@app.get("/hit")
def hello():
    count = get_hit_count()
    return "Hello World! I have been seen {} times.".format(count)


@app.get("/users", response_model=list[UserResponse])
async def users():
    """List all users."""
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token."""
    token = credentials.credentials
    async with async_session() as session:
        result = await session.execute(select(User).where(User.api_key == token))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return user


@app.post("/task", response_model=TaskResponseBase)
def create_task(x: int = Query(...), y: int = Query(...), user: User = Depends(get_current_user)):
    """Create a number addition task."""
    task = celery_app.send_task("worker.add", args=[x, y])
    return TaskResponseBase(task_id=task.id)


@app.get("/poll", response_model=TaskResponseState)
def poll_task(task_id: str = Query(...)):
    """Poll task state."""
    result = celery_app.AsyncResult(task_id)
    response = TaskResponseState(task_id=task_id, state=result.state)
    if result.ready():
        response.result = result.result
    return response
