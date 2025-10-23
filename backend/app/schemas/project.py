"""
Project Pydantic schemas
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    technologies: Optional[List[str]] = []
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    company_id: Optional[str] = None
    featured: Optional[bool] = False
    order_index: Optional[int] = 0

    # Additional media fields
    video_url: Optional[str] = None
    video_title: Optional[str] = None
    map_url: Optional[str] = None
    map_title: Optional[str] = None
    responsibilities: Optional[List[str]] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    technologies: Optional[List[str]] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    company_id: Optional[str] = None
    featured: Optional[bool] = None
    order_index: Optional[int] = None

    # Additional media fields
    video_url: Optional[str] = None
    video_title: Optional[str] = None
    map_url: Optional[str] = None
    map_title: Optional[str] = None
    responsibilities: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('technologies', mode='before')
    @classmethod
    def validate_technologies(cls, v):
        """Convert string to list if necessary"""
        if v is None:
            return []
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [tech.strip() for tech in v.split(',') if tech.strip()]
        return v

    @field_validator('responsibilities', mode='before')
    @classmethod
    def validate_responsibilities(cls, v):
        """Convert string to list if necessary"""
        if v is None:
            return None
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [resp.strip() for resp in v.split(',') if resp.strip()]
        return v

    class Config:
        from_attributes = True