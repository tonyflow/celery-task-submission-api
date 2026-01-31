from pydantic import BaseModel


class UserResponse(BaseModel):
    """User response model."""

    name: str
    """User name"""


class TaskResponseBase(BaseModel):
    """Task response base model."""

    task_id: str
    """Task id."""


class TaskResponseState(TaskResponseBase):
    """Task response state and result."""

    state: str
    """Task state."""

    result: int | None = None
    """Task result."""
