"""
Project model
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    # Type-checker-only to avoid the Company <-> Project import cycle;
    # SQLAlchemy resolves "Company" from its declarative registry.
    from app.models.company import Company


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    detailed_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # List of technologies used
    technologies: Mapped[Any] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    github_url: Mapped[str | None] = mapped_column(String(500))
    live_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    company_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    order_index: Mapped[int | None] = mapped_column(Integer, default=0, index=True)

    # Additional media fields
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    map_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    map_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsibilities: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    # Timestamps — DB-01: server_default on updated_at so INSERTs populate
    # the column instead of leaving it NULL until first UPDATE.
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company | None"] = relationship("Company", back_populates="projects")
