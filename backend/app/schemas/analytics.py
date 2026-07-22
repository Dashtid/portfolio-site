"""
Pydantic schemas for analytics
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PageViewCreate(BaseModel):
    """Schema for creating a page view record."""

    # Generous caps: campaign/UTM URLs legitimately exceed 500 chars, and
    # rejecting the beacon would lose the visit entirely. Values are
    # truncated to the String(500) PageView columns at insert (see
    # track_pageview) — letting them through untruncated raises Postgres
    # 22001 (value too long) from an unauthenticated endpoint.
    page_path: str = Field(..., max_length=2048)
    page_title: str | None = Field(None, max_length=512)
    referrer: str | None = Field(None, max_length=2048)
    visitor_id: str | None = Field(None, max_length=128)  # Session ID from frontend


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


class OutboundClick(BaseModel):
    """Aggregated outbound-link clicks.

    Sourced from the synthetic '/event/outbound/<dest>/<label>' page views the
    frontend records via trackEvent, aggregated separately so they stay OUT of
    the real page-view metrics (D3-M-01: honest signals).
    """

    destination: str
    count: int


class AnalyticsStats(BaseModel):
    """Schema for analytics summary stats."""

    total_views: int
    unique_visitors: int
    avg_session_duration: int  # in seconds
    top_pages: list[TopPage]
    daily_views: list[DailyView]
    period_days: int
    # Optional + defaulted so older clients keep working; page-view metrics
    # above deliberately exclude these synthetic '/event/' rows.
    outbound_clicks: list[OutboundClick] = Field(default_factory=list)


class VisitorInfo(BaseModel):
    """Schema for visitor information."""

    visitor_id: str
    first_visit: datetime
    last_visit: datetime
    page_views: int

    model_config = {"from_attributes": True}


class TopCountry(BaseModel):
    """Schema for per-country visitor counts."""

    country: str
    count: int


class VisitorStats(BaseModel):
    """Schema for the visitor stats endpoint response."""

    total_sessions: int
    new_visitors: int
    returning_visitors: int
    avg_session_duration: int | None
    bounce_rate: float | None
    top_countries: list[TopCountry]
    period_days: int
