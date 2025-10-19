"""
Analytics API endpoints for tracking visitor statistics
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.database import get_db
from app.models.analytics import PageView, VisitorSession
from app.schemas.analytics import PageViewCreate, AnalyticsStats
import hashlib
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_visitor_id(request: Request) -> str:
    """Generate a visitor ID from request information."""
    # Use IP + User-Agent for basic visitor identification
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    visitor_string = f"{ip}:{user_agent}"
    return hashlib.sha256(visitor_string.encode()).hexdigest()[:16]


@router.post("/track/pageview")
async def track_pageview(
    pageview: PageViewCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Track a page view."""
    try:
        visitor_id = get_visitor_id(request)

        # Create or update visitor session
        session_result = await db.execute(
            select(VisitorSession).where(VisitorSession.visitor_id == visitor_id)
        )
        visitor_session = session_result.scalar_one_or_none()

        if not visitor_session:
            # New visitor
            visitor_session = VisitorSession(
                visitor_id=visitor_id,
                first_visit=datetime.utcnow(),
                last_visit=datetime.utcnow(),
                page_views=0,
                user_agent=request.headers.get("user-agent", "")[:500],
                ip_address=request.client.host
            )
            db.add(visitor_session)

        # Update session
        visitor_session.last_visit = datetime.utcnow()
        visitor_session.page_views += 1

        # Record page view
        page_view = PageView(
            visitor_id=visitor_id,
            page_path=pageview.page_path,
            page_title=pageview.page_title,
            referrer=pageview.referrer,
            timestamp=datetime.utcnow(),
            user_agent=request.headers.get("user-agent", "")[:500],
            ip_address=request.client.host
        )
        db.add(page_view)

        await db.commit()
        return {"status": "success", "visitor_id": visitor_id}

    except Exception as e:
        logger.error(f"Error tracking page view: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to track page view")


@router.get("/stats/summary", response_model=AnalyticsStats)
async def get_analytics_summary(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics summary for the specified period."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total page views
        total_views_result = await db.execute(
            select(func.count(PageView.id)).where(PageView.timestamp >= cutoff_date)
        )
        total_views = total_views_result.scalar() or 0

        # Unique visitors
        unique_visitors_result = await db.execute(
            select(func.count(func.distinct(PageView.visitor_id))).where(
                PageView.timestamp >= cutoff_date
            )
        )
        unique_visitors = unique_visitors_result.scalar() or 0

        # Top pages
        top_pages_result = await db.execute(
            select(
                PageView.page_path,
                PageView.page_title,
                func.count(PageView.id).label("views")
            )
            .where(PageView.timestamp >= cutoff_date)
            .group_by(PageView.page_path, PageView.page_title)
            .order_by(desc("views"))
            .limit(10)
        )
        top_pages = [
            {
                "path": row.page_path,
                "title": row.page_title,
                "views": row.views
            }
            for row in top_pages_result
        ]

        # Views by day
        daily_views_result = await db.execute(
            select(
                func.date(PageView.timestamp).label("date"),
                func.count(PageView.id).label("views")
            )
            .where(PageView.timestamp >= cutoff_date)
            .group_by("date")
            .order_by("date")
        )
        daily_views = [
            {
                "date": str(row.date),
                "views": row.views
            }
            for row in daily_views_result
        ]

        # Average session duration (simplified)
        avg_session_duration = 180  # Default 3 minutes

        return AnalyticsStats(
            total_views=total_views,
            unique_visitors=unique_visitors,
            avg_session_duration=avg_session_duration,
            top_pages=top_pages,
            daily_views=daily_views,
            period_days=days
        )

    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.get("/stats/visitors")
async def get_visitor_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed visitor statistics."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Recent visitors
        recent_visitors_result = await db.execute(
            select(VisitorSession)
            .where(VisitorSession.last_visit >= cutoff_date)
            .order_by(desc(VisitorSession.last_visit))
            .limit(50)
        )
        recent_visitors = [
            {
                "visitor_id": v.visitor_id,
                "first_visit": v.first_visit.isoformat(),
                "last_visit": v.last_visit.isoformat(),
                "page_views": v.page_views
            }
            for v in recent_visitors_result.scalars()
        ]

        # Returning visitors
        returning_visitors_result = await db.execute(
            select(func.count(VisitorSession.id))
            .where(VisitorSession.page_views > 1)
            .where(VisitorSession.last_visit >= cutoff_date)
        )
        returning_visitors = returning_visitors_result.scalar() or 0

        return {
            "recent_visitors": recent_visitors,
            "returning_visitors": returning_visitors,
            "period_days": days
        }

    except Exception as e:
        logger.error(f"Error getting visitor stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get visitor stats")


@router.delete("/stats/clear")
async def clear_analytics(
    older_than_days: int = 90,
    db: AsyncSession = Depends(get_db)
):
    """Clear old analytics data."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Delete old page views
        await db.execute(
            select(PageView).where(PageView.timestamp < cutoff_date).delete()
        )

        # Delete old sessions
        await db.execute(
            select(VisitorSession).where(VisitorSession.last_visit < cutoff_date).delete()
        )

        await db.commit()
        return {"status": "success", "message": f"Cleared data older than {older_than_days} days"}

    except Exception as e:
        logger.error(f"Error clearing analytics: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to clear analytics")