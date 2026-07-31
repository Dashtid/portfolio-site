"""
User model for authentication
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User model for authentication"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # DB-05: bounded lengths. GitHub user IDs are 64-bit ints stored as
    # strings (≤20 chars realistically); usernames are capped at 39 chars by
    # GitHub policy; email follows the RFC 5321 254-char ceiling. Unbounded
    # VARCHAR has no practical cost on SQLite but materialises as TEXT on
    # Postgres, which prevents index optimisations and makes accidental
    # multi-MB inserts possible.
    github_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(39), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # is_admin must be NOT NULL: any privilege check in the code shape
    # `if user.is_admin: ...` treats NULL as falsy, but a raw INSERT that
    # forgot to set the column would leave it NULL and the next ORM read
    # would behave unpredictably. server_default ensures the DB picks False
    # even on out-of-band inserts (e.g. seed scripts, migrations).
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.false()
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # DB-01: server_default on updated_at so an INSERT also populates the
    # column instead of leaving it NULL until the first UPDATE; onupdate
    # keeps moving it forward on subsequent UPDATEs.
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
