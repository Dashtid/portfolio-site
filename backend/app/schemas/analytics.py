"""
Pydantic schemas for analytics
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict


class PageViewCreate(BaseModel):
    """Schema for creating a page view record."""
    page_path: str
    page_title: Optional[str] = None
    referrer: Optional[str] = None


class PageViewResponse(BaseModel):
    """Response schema for page view."""
    id: int
    visitor_id: str
    page_path: str
    page_title: Optional[str]
    referrer: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class TopPage(BaseModel):
    """Schema for top pages stats."""
    path: str
    title: Optional[str]
    views: int


class DailyView(BaseModel):
    """Schema for daily view counts."""
    date: str
    views: int


class AnalyticsStats(BaseModel):
    """Schema for analytics summary stats."""
    total_views: int
    unique_visitors: int
    avg_session_duration: int  # in seconds
    top_pages: List[TopPage]
    daily_views: List[DailyView]
    period_days: int


class VisitorInfo(BaseModel):
    """Schema for visitor information."""
    visitor_id: str
    first_visit: datetime
    last_visit: datetime
    page_views: int

    class Config:
        from_attributes = True