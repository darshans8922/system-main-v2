"""
Database models aligned with the legacy FastAPI service.
"""
from sqlalchemy import Column, Integer, String

from app.database import Base


class User(Base):
    """
    Minimal user representation sourced from public.app_users.
    """

    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)

