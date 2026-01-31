from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    api_key = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    credits = Column(Integer, nullable=False)
