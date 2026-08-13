"""
CV profile (singleton) model.

Backs the admin-only "Export CV" feature (Campaign 2026-08 Sprint 2). The
public site IS the CV — there is no public /cv page. The downloadable CV is
assembled from the DB the owner already curates through the admin CMS
(companies = experience, education, skills) PLUS the prose and contact that
have no other home: summary, headline, focus, languages, and the owner's
private contact details.

This table is the ONLY place the owner's private contact (email / phone,
optional personnummer) is stored, and it is exposed solely through
admin-authenticated endpoints (app/api/v1/cv.py) — never a public
serializer, the SSG bundle, or any unauthenticated /api/v1 route.

Singleton: a single row (id=1). _get_or_create_profile() in the router owns
that invariant.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CvProfile(Base):
    __tablename__ = "cv_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Public-safe profile prose (mirrors JSON Resume `basics`). These are the
    # fields with no other DB home; experience/education/skills live in their
    # own tables and are assembled at export time.
    name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    label: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    focus: Mapped[str] = mapped_column(Text, nullable=False, default="")
    location_city: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    location_region: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    # ISO 3166-1 alpha-2
    location_country: Mapped[str] = mapped_column(String(2), nullable=False, default="")
    url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    linkedin_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    github_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    # [{"language": "...", "fluency": "..."}] — there is no separate language
    # table; the CV needs only this small flat list.
    languages: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)
    # Övrigt / logistics one-liners (e.g. "B-körkort (category B driving
    # licence)") rendered at the BOTTOM of the CV under "Other". Deliberately
    # its own column, not an education/certification row: the CV-generator
    # requirements (2026-08-06) forbid logistics facts from ever being
    # classified as credentials, and a separate column makes that structural.
    other_items: Mapped[Any] = mapped_column(JSON, nullable=False, default=list)

    # Private contact — admin-only. NEVER surfaced on a public serializer, the
    # SSG bundle, or any unauthenticated route. Blank by default and populated
    # by the owner through the admin CV form after deploy, so the real values
    # are never committed to the repo. personnummer is optional and off by
    # default (data minimisation — modern Swedish CVs omit it, and it is
    # needless identity-theft exposure to store unless an employer requires it).
    email: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    personnummer: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
