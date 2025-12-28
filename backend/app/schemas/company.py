"""
Company Pydantic schemas
"""

import re
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

# Pattern for safe URLs: http(s)://, relative paths, or None
# Blocks javascript:, data:, vbscript: and other XSS vectors
SAFE_URL_PATTERN = re.compile(r"^(https?://|/[^/]|$)")


def validate_safe_url(v: str | None, field_name: str) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError(f"{field_name} must be an HTTP(S) URL or relative path starting with /")
    return v


class CompanyBase(BaseModel):
    name: str
    title: str | None = None
    description: str | None = None
    detailed_description: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    logo_url: str | None = None
    website: str | None = None
    order_index: int | None = 0
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = Field(None, max_length=50)  # Max 50 items
    technologies: list[str] | None = Field(None, max_length=100)  # Max 100 items

    @field_validator("logo_url", "website", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")

    @field_validator("responsibilities", "technologies", mode="before")
    @classmethod
    def validate_list_items(cls, v: list[str] | None) -> list[str] | None:
        """Validate list items have reasonable length."""
        if v is None:
            return v
        for item in v:
            if len(item) > 200:
                raise ValueError("List item exceeds maximum length of 200 characters")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    description: str | None = None
    detailed_description: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    logo_url: str | None = None
    website: str | None = None
    order_index: int | None = None
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = Field(None, max_length=50)  # Max 50 items
    technologies: list[str] | None = Field(None, max_length=100)  # Max 100 items

    @field_validator("logo_url", "website", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")

    @field_validator("responsibilities", "technologies", mode="before")
    @classmethod
    def validate_list_items(cls, v: list[str] | None) -> list[str] | None:
        """Validate list items have reasonable length."""
        if v is None:
            return v
        for item in v:
            if len(item) > 200:
                raise ValueError("List item exceeds maximum length of 200 characters")
        return v


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
