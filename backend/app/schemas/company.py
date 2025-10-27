"""
Company Pydantic schemas
"""

from datetime import date, datetime

from pydantic import BaseModel


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
    responsibilities: list[str] | None = None
    technologies: list[str] | None = None


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
    responsibilities: list[str] | None = None
    technologies: list[str] | None = None


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
