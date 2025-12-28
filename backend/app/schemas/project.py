"""
Project Pydantic schemas
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Pattern for safe URLs: http(s)://, relative paths, or None
# Blocks javascript:, data:, vbscript: and other XSS vectors
SAFE_URL_PATTERN = re.compile(r"^(https?://|/[^/]|$)")

# Maximum items in list fields to prevent DoS
MAX_TECHNOLOGIES = 50
MAX_RESPONSIBILITIES = 50


def validate_safe_url(v: str | None, field_name: str) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError(f"{field_name} must be an HTTP(S) URL or relative path starting with /")
    return v


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    detailed_description: str | None = Field(None, max_length=10000)
    technologies: list[str] | None = Field(default=[], max_length=MAX_TECHNOLOGIES)
    github_url: str | None = None
    live_url: str | None = None
    image_url: str | None = None
    company_id: str | None = None
    featured: bool | None = False
    order_index: int | None = 0

    # Additional media fields
    video_url: str | None = None
    video_title: str | None = Field(None, max_length=200)
    map_url: str | None = None
    map_title: str | None = Field(None, max_length=200)
    responsibilities: list[str] | None = Field(None, max_length=MAX_RESPONSIBILITIES)

    @field_validator("github_url", "live_url", "image_url", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    detailed_description: str | None = Field(None, max_length=10000)
    technologies: list[str] | None = Field(None, max_length=MAX_TECHNOLOGIES)
    github_url: str | None = None
    live_url: str | None = None
    image_url: str | None = None
    company_id: str | None = None
    featured: bool | None = None
    order_index: int | None = None

    # Additional media fields
    video_url: str | None = None
    video_title: str | None = Field(None, max_length=200)
    map_url: str | None = None
    map_title: str | None = Field(None, max_length=200)
    responsibilities: list[str] | None = Field(None, max_length=MAX_RESPONSIBILITIES)

    @field_validator("github_url", "live_url", "image_url", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator("technologies", mode="before")
    @classmethod
    def validate_technologies(cls, v):
        """Convert string to list if necessary"""
        if v is None:
            return []
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [tech.strip() for tech in v.split(",") if tech.strip()]
        return v

    @field_validator("responsibilities", mode="before")
    @classmethod
    def validate_responsibilities(cls, v):
        """Convert string to list if necessary"""
        if v is None:
            return None
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [resp.strip() for resp in v.split(",") if resp.strip()]
        return v

    model_config = {"from_attributes": True}
