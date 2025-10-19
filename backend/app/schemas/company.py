"""
Company Pydantic schemas
"""
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import date, datetime


class CompanyBase(BaseModel):
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    order_index: Optional[int] = 0


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    order_index: Optional[int] = None


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True