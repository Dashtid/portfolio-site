"""
Pydantic schemas for analytics
"""

from datetime import datetime

from pydantic import BaseModel


class PageViewCreate(BaseModel):
    """Schema for creating a page view record."""

    page_path: str
    page_title: str | None = None
    referrer: str | None = None
    visitor_id: str | None = None  # Session ID from frontend


class PageViewResponse(BaseModel):
    """Response schema for page view."""

    id: str
    visitor_id: str
    page_path: str
    page_title: str | None
    referrer: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}


class TopPage(BaseModel):
    """Schema for top pages stats."""

    path: str
    title: str | None
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
    top_pages: list[TopPage]
    daily_views: list[DailyView]
    period_days: int


class VisitorInfo(BaseModel):
    """Schema for visitor information."""

    visitor_id: str
    first_visit: datetime
    last_visit: datetime
    page_views: int

    model_config = {"from_attributes": True}
