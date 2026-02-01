import redis
import logging
from celery import Celery
from fastapi import FastAPI, Query, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update

from database.engine import async_session
from database.models import User
from models import UserResponse, TaskResponseBase, TaskResponseState, UserCreditsResponse

cache = redis.Redis(host="redis", port=6379)
celery_app = Celery("worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://redis:6379/0")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_logger = logging.getLogger(__name__)

API_COST = 10
"""Arbitrary API cost for each task submitted."""
app = FastAPI()

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from token.

    Utility function to retrieve the user trying to access the API based on the provided bearer
    token.
    """
    token = credentials.credentials
    async with async_session() as session:
        result = await session.execute(select(User).where(User.api_key == token))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return user


@app.get("/users", response_model=list[UserResponse])
async def users():
    """List all users."""
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


@app.post("/task", response_model=TaskResponseBase)
async def create_task(x: int = Query(...),
                      y: int = Query(...),
                      user: User = Depends(get_current_user)):
    """Create a number addition task."""
    if user.credits - API_COST < 0:
        raise HTTPException(status_code=403, detail="Insufficient credits")

    async with async_session() as session:
        session.execute(update(User).where(User.name == user.name)
        .values(credits=user.credits - API_COST))

    task = celery_app.send_task("worker.add", args=[x, y])
    return TaskResponseBase(task_id=task.id)


@app.get("/poll", response_model=TaskResponseState)
def poll_task(task_id: str = Query(...)):
    """Poll task state.

    :arg task_id: Task id.
    """
    result = celery_app.AsyncResult(task_id)
    response = TaskResponseState(task_id=task_id, state=result.state)
    if result.ready():
        response.result = result.result
    return response


@app.put("/credits/{user_name}", response_model=UserCreditsResponse)
async def update_user_credits(user_name: str,
                              api_credits: int = Query(...),
                              user: User = Depends(get_current_user)):
    """Update a user's API credits.

    Only admin users have access to this API.
    """
    if user.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can update credits.")

    _logger.info(f"Updating user {user.name} with {api_credits} credits")

    async with async_session() as session:
        result = await session.execute(
            update(User).where(User.name == user_name)
            .values(credits=api_credits)
            .returning(User.name, User.credits)
        )

        affected_user = result.fetchone()

        if affected_user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        await session.commit()

        return UserCreditsResponse(name=affected_user.name, credits=affected_user.credits)
