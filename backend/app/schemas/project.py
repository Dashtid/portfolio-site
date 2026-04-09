"""
Project Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas._validators import validate_safe_url

# Maximum items in list fields to prevent DoS
MAX_TECHNOLOGIES = 50
MAX_RESPONSIBILITIES = 50


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    detailed_description: str | None = Field(None, max_length=10000)
    technologies: list[str] = Field(default_factory=list, max_length=MAX_TECHNOLOGIES)
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
    @field_validator("technologies", mode="before")
    @classmethod
    def validate_technologies_input(cls, v):
        """Reject non-list input and validate each item on the create path."""
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("technologies must be a list")
        for item in v:
            if not isinstance(item, str):
                raise ValueError("each technology must be a string")
            if len(item) > 100:
                raise ValueError("technology name exceeds 100 characters")
        return v


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

    @field_validator("technologies", mode="before")
    @classmethod
    def validate_technologies_input(cls, v):
        """Reject non-list input and validate each item on the update path."""
        if v is None:
            return None  # None means "do not update this field"
        if not isinstance(v, list):
            raise ValueError("technologies must be a list")
        for item in v:
            if not isinstance(item, str):
                raise ValueError("each technology must be a string")
            if len(item) > 100:
                raise ValueError("technology name exceeds 100 characters")
        return v


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
