"""
User model for authentication
"""

import uuid

import sqlalchemy as sa
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
    # is_admin must be NOT NULL: any privilege check in the code shape
    # `if user.is_admin: ...` treats NULL as falsy, but a raw INSERT that
    # forgot to set the column would leave it NULL and the next ORM read
    # would behave unpredictably. server_default ensures the DB picks False
    # even on out-of-band inserts (e.g. seed scripts, migrations).
    is_admin = Column(Boolean, nullable=False, default=False, server_default=sa.false())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
