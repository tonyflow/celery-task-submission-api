import logging

from fastapi import FastAPI, Query, HTTPException
from fastapi.params import Depends

import auth
import service
from database.models import User
from models import UserResponseBase, TaskResponseBase, TaskStateResponse, UserCreditsResponse


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/users", response_model=list[UserResponseBase])
async def users():
    """List all users."""
    return await service.get_all_users()


@app.post("/task", response_model=TaskResponseBase)
async def create_addition_task(x: int = Query(...),
                               y: int = Query(...),
                               user: User = Depends(auth.get_current_user)):
    """Create a number addition task."""
    return await service.create_addition_task(user, x, y)


@app.get("/poll/{task_id}", response_model=TaskStateResponse)
def poll_task_state(task_id: str):
    """Poll task state.

    The endpoint will only populate the `result` part of the response if the underlying
    task has been completed successfully. Otherwise, only the task ID with the corresponding state
    will be returned.
    """
    return service.poll_task_state(task_id)


@app.get("/fair_poll/{task_id}", response_model=TaskStateResponse)
async def fair_poll_task(task_id: str, user: User = Depends(auth.get_current_user)):
    """Poll task state.

    This endpoint uses a "fairer" approach to polling task states and deducting credits.

    The endpoint will only populate the `result` part of the response if the underlying
    task has been completed successfully. Otherwise, only the task ID with the corresponding state
    will be returned.
    """
    return await service.fair_poll_task_state(user, task_id)


@app.get("/credits/{user_name}", response_model=UserCreditsResponse)
async def get_user_credits(user_name: str,
                           user: User = Depends(auth.get_current_user)):
    """Retrieve a user's credits.

    Only admin users have access to this API.
    """
    if user.name != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can update credits.")

    _logger.debug(f"Retrieving credits for {user.name}.")

    return await service.get_user_credits(user_name)


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

    return await service.update_user_credits(user_name, api_credits)
