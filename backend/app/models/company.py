"""
Company/Experience model
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    # Import-time cycle (Project imports Company for its own back-reference),
    # so this is type-checker-only; SQLAlchemy resolves "Project" from its
    # declarative registry at mapper-configuration time.
    from app.models.project import Project


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    # Extended description for detail page
    detailed_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # Null means current job
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(500))
    order_index: Mapped[int | None] = mapped_column(Integer, default=0, index=True)

    # Detail page media
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # YouTube embed URL
    video_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    map_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Google Maps embed URL
    map_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Structured data for detail page
    # List of responsibilities
    responsibilities: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    technologies: Mapped[Any | None] = mapped_column(JSON, nullable=True)  # Technologies used
    # List of quantified outcome bullets (D3-UX-03)
    outcomes: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    # Curated CV bullets — 1-3 per role, deliberately SEPARATE from the two
    # lists above. Those describe the role for the public detail page, where
    # they render as distinct blocks; a CV needs a short, past-tense selection.
    # Concatenating responsibilities + outcomes for the CV produced 64 bullets
    # across 8 roles with heavy restatement. NULL means "fall back" (see the
    # export in api/v1/cv.py), so a new role still exports something sane.
    cv_highlights: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    # Timestamps — DB-01: server_default on updated_at so INSERTs populate
    # the column instead of leaving it NULL until first UPDATE.
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="company", cascade="all, delete-orphan"
    )
