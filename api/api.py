import logging

import redis
from fastapi import FastAPI, Query, HTTPException
from fastapi.params import Depends
from fastapi.security import HTTPBearer

import auth
import service
from database.models import User
from models import UserResponseBase, TaskResponseBase, TaskStateResponse, UserCreditsResponse

cache = redis.Redis(host="redis", port=6379)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_logger = logging.getLogger(__name__)

app = FastAPI()

security = HTTPBearer()


@app.get("/users", response_model=list[UserResponseBase])
async def users():
    """List all users."""
    return service.get_all_users()


@app.post("/task", response_model=TaskResponseBase)
async def create_addition_task(x: int = Query(...),
                      y: int = Query(...),
                      user: User = Depends(auth.get_current_user)):
    """Create a number addition task."""
    return service.create_addition_task(user, x, y)


@app.get("/poll/{task_id}", response_model=TaskStateResponse)
def poll_task_state(task_id: str):
    """Poll task state."""
    return service.poll_task_state(task_id)


@app.get("/fair_poll/{task_id}", response_model=TaskStateResponse)
async def fair_poll_task(task_id: str = Query(...), user: User = Depends(auth.get_current_user)):
    return service.fair_poll_task_state(user, task_id)


@app.get("/credits/{user_name}", response_model=UserCreditsResponse)
async def get_user_credits(user_name: str,
                           user: User = Depends(auth.get_current_user)):
    """Get a user's credits.

    Only admin users have access to this API.
    """
    if user.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can update credits.")

    _logger.debug(f"Retrieving credits for {user.name}.")

    return service.get_user_credits(user_name)


@app.put("/credits/{user_name}", response_model=UserCreditsResponse)
async def update_user_credits(user_name: str,
                              api_credits: int = Query(...),
                              user: User = Depends(auth.get_current_user)):
    """Update a user's API credits.

    Only admin users have access to this API.
    """
    if user.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can update credits.")

    _logger.debug(f"Updating user {user.name} with {api_credits} credits")


