from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """User model."""
    __tablename__ = "users"

    api_key = Column(String(36), primary_key=True)
    """API key."""

    name = Column(String(255), nullable=False)
    """Name."""

    credits = Column(Integer, nullable=False)
    """Credits."""
