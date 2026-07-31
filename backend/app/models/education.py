from datetime import date

from sqlalchemy import Boolean, Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Education(Base):
    __tablename__ = "education"

    # DB-09: PRIMARY KEY already implies an index; the explicit index=True
    # was a duplicate. Dropped.
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))  # Institution logo
    # DB-02: indexed because the public listing and detail pages split on
    # is_certification (degrees vs. certifications); a small index pays off
    # even at low cardinality given how often this column is filtered on.
    is_certification: Mapped[bool | None] = mapped_column(Boolean, default=False, index=True)
    certificate_number: Mapped[str | None] = mapped_column(String(100))
    # URL to certificate/credential
    certificate_url: Mapped[str | None] = mapped_column(String(500))
    # For custom sorting (renamed from 'order' for consistency)
    order_index: Mapped[int | None] = mapped_column(Integer, default=0, index=True)
