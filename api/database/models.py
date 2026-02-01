import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"

    name = Column(String(255), primary_key=True, nullable=False)
    """Username."""

    api_key = Column(String(36), nullable=False)
    """API key."""

    credits = Column(Integer, nullable=False)
    """User credits.

    These credits are deducted from the user every time they use the API.
    """

    task_history = relationship("UserTaskHistory", back_populates="user")


class UserTaskHistory(Base):
    """User task history model."""
    __tablename__ = "user_task_history"

    user_name = Column(String(255), ForeignKey("users.name"), primary_key=True, nullable=False)
    """Username of the user who performed the task."""

    task_id = Column(String(255), primary_key=True, nullable=False)
    """Task ID."""

    cost = Column(Integer, nullable=False)
    """Cost of task in credits."""

    created_at = Column(DateTime, nullable=False, default=func.now())
    """Timestamp of when the task was performed."""

    # Relations
    user = relationship("User", back_populates="task_history")
