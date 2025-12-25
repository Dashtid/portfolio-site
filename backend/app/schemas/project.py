"""
Project Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, field_validator


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    detailed_description: str | None = None
    technologies: list[str] | None = []
    github_url: str | None = None
    live_url: str | None = None
    image_url: str | None = None
    company_id: str | None = None
    featured: bool | None = False
    order_index: int | None = 0

    # Additional media fields
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    detailed_description: str | None = None
    technologies: list[str] | None = None
    github_url: str | None = None
    live_url: str | None = None
    image_url: str | None = None
    company_id: str | None = None
    featured: bool | None = None
    order_index: int | None = None

    # Additional media fields
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = None


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
