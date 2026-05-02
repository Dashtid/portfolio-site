"""
Analytics API endpoints for tracking visitor statistics

Provides endpoints for:
- Tracking page views (public)
- Getting analytics summary (admin)
- Getting visitor statistics (admin)
"""

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.core.geo_ip import get_country_code
from app.core.ip_utils import get_client_ip
from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.analytics import PageView
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsStats,
    DailyView,
    PageViewCreate,
    PageViewResponse,
    TopCountry,
    TopPage,
    VisitorStats,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Type aliases
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.post("/track/pageview", response_model=PageViewResponse)
@rate_limit_public
async def track_pageview(
    request: Request,
    page_view: PageViewCreate,
    db: DbSession,
):
    """
    Track a page view (public endpoint).

    Records visitor page views for analytics. The raw client IP is hashed
    before persistence (GDPR pseudonymisation) and looked up against ipapi.co
    for a country code; the lookup is best-effort and caches results for 24h.
    """
    # Get client IP securely (only trusts X-Forwarded-For from known proxies)
    client_ip = get_client_ip(request)

    # Determine session_id: use visitor_id from frontend, or generate from IP hash
    if page_view.visitor_id:
        session_id = page_view.visitor_id
    else:
        # Fallback: generate anonymous session from IP hash (for privacy)
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
        session_id = f"anon_{ip_hash}"

    # Resolve country before persisting. Lookup is best-effort: timeouts and
    # upstream failures return None and the row is still written.
    country = await get_country_code(client_ip)

    db_pageview = PageView(
        page_path=page_view.page_path,
        referrer=page_view.referrer,
        user_agent=request.headers.get("User-Agent"),
        ip_address=hashlib.sha256(client_ip.encode()).hexdigest()[:16],
        country=country,
        session_id=session_id,
    )
    db.add(db_pageview)
    await db.commit()
    await db.refresh(db_pageview)

    return PageViewResponse(
        id=str(db_pageview.id),
        visitor_id=str(db_pageview.session_id) if db_pageview.session_id else "anonymous",
        page_path=str(db_pageview.page_path),
        page_title=None,
        referrer=str(db_pageview.referrer) if db_pageview.referrer else None,
        timestamp=db_pageview.created_at or datetime.now(UTC),  # type: ignore[arg-type]
    )


@router.get("/stats/summary", response_model=AnalyticsStats)
async def get_analytics_summary(
    db: DbSession,
    current_user: AdminUser,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include in summary"),
):
    """
    Get analytics summary (admin only).
    Returns total views, unique visitors, top pages, and daily views.
    """
    _ = current_user  # Used for authentication

    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Total page views
    total_result = await db.execute(
        select(func.count(PageView.id)).where(PageView.created_at >= cutoff)
    )
    total_views = total_result.scalar() or 0

    # Unique visitors (by session_id)
    unique_result = await db.execute(
        select(func.count(func.distinct(PageView.session_id))).where(PageView.created_at >= cutoff)
    )
    unique_visitors = unique_result.scalar() or 0

    # Top pages
    top_pages_result = await db.execute(
        select(PageView.page_path, func.count(PageView.id).label("views"))
        .where(PageView.created_at >= cutoff)
        .group_by(PageView.page_path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    top_pages = [
        TopPage(path=row.page_path, title=None, views=row.views) for row in top_pages_result.all()
    ]

    # Daily views (last N days)
    daily_views_result = await db.execute(
        select(
            func.date(PageView.created_at).label("date"),
            func.count(PageView.id).label("views"),
        )
        .where(PageView.created_at >= cutoff)
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
    )
    daily_views = [
        DailyView(date=str(row.date), views=row.views) for row in daily_views_result.all()
    ]

    return AnalyticsStats(
        total_views=total_views,
        unique_visitors=unique_visitors,
        avg_session_duration=0,  # Would require session tracking
        top_pages=top_pages,
        daily_views=daily_views,
        period_days=days,
    )


@router.get("/stats/visitors", response_model=VisitorStats)
async def get_visitor_stats(
    db: DbSession,
    current_user: AdminUser,
    days: int = Query(default=7, ge=1, le=365, description="Number of days to include in stats"),
) -> VisitorStats:
    """
    Get visitor statistics (admin only).
    Returns session counts, geographic data, and visitor trends.
    """
    _ = current_user  # Used for authentication

    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Total sessions
    sessions_result = await db.execute(
        select(func.count(func.distinct(PageView.session_id))).where(PageView.created_at >= cutoff)
    )
    total_sessions = sessions_result.scalar() or 0

    # Top countries
    countries_result = await db.execute(
        select(PageView.country, func.count(PageView.id).label("count"))
        .where(PageView.created_at >= cutoff, PageView.country.isnot(None))
        .group_by(PageView.country)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    top_countries = [
        TopCountry(country=row.country, count=row.count) for row in countries_result.all()
    ]

    return VisitorStats(
        total_sessions=total_sessions,
        new_visitors=total_sessions,  # Simplified — would need first-visit tracking
        returning_visitors=0,
        avg_session_duration=None,
        bounce_rate=None,
        top_countries=top_countries,
        period_days=days,
    )
