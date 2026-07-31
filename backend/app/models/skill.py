"""
Skill/Technology model
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    # 'language', 'framework', 'tool', 'database', etc.
    category: Mapped[str | None] = mapped_column(String(50))
    proficiency_level: Mapped[int | None] = mapped_column(Integer)  # 0-100 percentage scale
    years_of_experience: Mapped[float | None] = mapped_column(Float)
    order_index: Mapped[int | None] = mapped_column(Integer, default=0, index=True)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
