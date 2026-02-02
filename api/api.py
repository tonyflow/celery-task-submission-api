import logging

from fastapi import FastAPI, Query, HTTPException
from fastapi.params import Depends

import auth
import service
from database.models import User
from models import UserResponseBase, TaskResponseBase, TaskStateResponse, UserCreditsResponse
from prometheus_fastapi_instrumentator import Instrumentator

from utils import deactivated

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_logger = logging.getLogger(__name__)

app = FastAPI()
"""FastAPI entrypoint."""

Instrumentator().instrument(app).expose(app)
"""Metrics endpoint.

The Prometheus FastAPI Instrumentator exposes a `/metrics` endpoint that can be used to
scrape metrics from the application. This endpoint is useful for monitoring the performance
and health of the application using Prometheus and Grafana.

The endpoint can be accessed under `http://localhost:8000/docs`
"""


@app.get("/health")
def health():
    """Health check endpoint.

    Only used for k8s liveliness probe currently.
    """
    return {"status": "ok"}


@app.get("/users", response_model=list[UserResponseBase])
async def users():
    """List all users."""

    _logger.debug("Listing all users")

    return await service.get_all_users()


@app.post("/task", response_model=TaskResponseBase)
async def create_addition_task(x: int = Query(...),
                               y: int = Query(...),
                               user: User = Depends(auth.get_current_user)):
    """Create a number addition task."""

    _logger.debug(f"Creating addition task with {x} and {y}")

    return await service.create_addition_task(user, x, y)


@app.get("/poll/{task_id}", response_model=TaskStateResponse)
def poll_task_state(task_id: str):
    """Poll task state.

    The endpoint will only populate the `result` part of the response if the underlying
    task has been completed successfully. Otherwise, only the task ID with the corresponding state
    will be returned.
    """

    _logger.debug(f"Polling task state for {task_id}")

    return service.poll_task_state(task_id)


@app.get("/fair_poll/{task_id}", response_model=TaskStateResponse)
@deactivated
async def fair_poll_task(task_id: str, user: User = Depends(auth.get_current_user)):
    """Poll task state.

    This endpoint uses a "fairer" approach to polling task states and deducting credits.

    The endpoint will only populate the `result` part of the response if the underlying
    task has been completed successfully. Otherwise, only the task ID with the corresponding state
    will be returned.

    The endpoint is temporarily deactivated!
    """
    _logger.debug(f"(Fair) Polling task state for {task_id}")

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
