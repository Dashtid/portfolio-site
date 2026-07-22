"""
Schemas for the admin-only CV profile (Campaign 2026-08 Sprint 2).

These schemas serve ONLY admin-authenticated endpoints, so the response
intentionally includes the private contact fields (email / phone /
personnummer) — an anonymous visitor can never reach them. Do not reuse
CvProfileResponse on any public route.
"""

from pydantic import BaseModel, Field


class LanguageItem(BaseModel):
    language: str = Field(..., min_length=1, max_length=100)
    fluency: str = Field("", max_length=100)


class CvProfileBase(BaseModel):
    # Public-safe prose
    name: str = Field("", max_length=200)
    label: str = Field("", max_length=300)
    summary: str = Field("", max_length=4000)
    focus: str = Field("", max_length=1000)
    location_city: str = Field("", max_length=120)
    location_region: str = Field("", max_length=120)
    location_country: str = Field("", max_length=2)
    url: str = Field("", max_length=500)
    linkedin_url: str = Field("", max_length=500)
    github_url: str = Field("", max_length=500)
    languages: list[LanguageItem] = Field(default_factory=list)

    # Private contact — only ever returned to the authenticated admin.
    email: str = Field("", max_length=320)
    phone: str = Field("", max_length=64)
    personnummer: str = Field("", max_length=64)


class CvProfileResponse(CvProfileBase):
    id: int

    model_config = {"from_attributes": True}


class CvProfileUpdate(BaseModel):
    """Partial update — only provided fields are applied (exclude_unset)."""

    name: str | None = Field(None, max_length=200)
    label: str | None = Field(None, max_length=300)
    summary: str | None = Field(None, max_length=4000)
    focus: str | None = Field(None, max_length=1000)
    location_city: str | None = Field(None, max_length=120)
    location_region: str | None = Field(None, max_length=120)
    location_country: str | None = Field(None, max_length=2)
    url: str | None = Field(None, max_length=500)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)
    languages: list[LanguageItem] | None = None
    email: str | None = Field(None, max_length=320)
    phone: str | None = Field(None, max_length=64)
    personnummer: str | None = Field(None, max_length=64)
