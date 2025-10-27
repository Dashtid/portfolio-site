"""
User model for authentication
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    github_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
