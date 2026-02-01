from pydantic import BaseModel


class UserResponseBase(BaseModel):
    """User response model."""

    name: str
    """User name"""

class UserCreditsResponse(UserResponseBase):
    """User response model."""

    credits: int
    """Leftover user credits."""


class TaskResponseBase(BaseModel):
    """Task response base model."""

    task_id: str
    """Task id."""


class TaskStateResponse(TaskResponseBase):
    """Task response state and result."""

    state: str
    """Task state."""

    result: int | None = None
    """Task result."""
