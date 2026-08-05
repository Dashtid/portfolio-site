"""
Analytics API endpoints for tracking visitor statistics

Provides endpoints for:
- Tracking page views (public)
- Getting analytics summary (admin)
- Getting visitor statistics (admin)
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.core.geo_ip import get_country_code
from app.core.ip_utils import get_client_ip
from app.database import AsyncSessionLocal, get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.analytics import PageView
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsStats,
    DailyView,
    OutboundClick,
    PageViewCreate,
    PageViewResponse,
    TopCountry,
    TopPage,
    VisitorStats,
)
from app.utils.ip_hash import hash_ip
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Type aliases
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


# C0 control characters (U+0000-U+001F) plus DEL. Postgres text columns
# cannot store U+0000 at all — asyncpg raises and the request 500s — and
# CR/LF in a value that later reaches a log line is log injection. Tabs
# and the rest of C0 carry no meaning in a URL path or a User-Agent, so
# the whole range goes.
_CONTROL_CHARS = dict.fromkeys(list(range(0x20)) + [0x7F])


def _scrub(value: str | None, limit: int) -> str | None:
    """Strip control characters and truncate to the column width.

    Returns None for None/empty input so optional columns stay NULL rather
    than becoming empty strings.
    """
    if not value:
        return None
    cleaned = value.translate(_CONTROL_CHARS)[:limit]
    return cleaned or None


async def _backfill_country(pageview_id: str, client_ip: str) -> None:
    """Resolve client_ip → country and write it onto the PageView row.

    PERF-01: previously the geo lookup blocked the response — ipapi.co's
    p50 is ~150ms and p99 can hit 1.5s on the free tier. Now the lookup
    runs after the response has been returned to the client, so the
    pageview-tracking endpoint becomes pure-DB (~5ms). The trade-off is
    the row is briefly committed with `country IS NULL` and back-filled
    seconds later; the analytics dashboard reads `WHERE country IS NOT
    NULL` so the NULL-window row only misses geo aggregation, not the
    visit count. Failures here are swallowed; country stays NULL.
    """
    try:
        country = await get_country_code(client_ip)
    except Exception:
        return
    if country is None:
        return
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                update(PageView).where(PageView.id == pageview_id).values(country=country)
            )
            await session.commit()
        except Exception:
            # No retry: a missed back-fill is OK; raising here would only
            # bloat error logs without changing user-visible behaviour.
            await session.rollback()


@router.post("/track/pageview", response_model=PageViewResponse)
@rate_limit_public
async def track_pageview(
    request: Request,
    page_view: PageViewCreate,
    db: DbSession,
    background_tasks: BackgroundTasks,
):
    """
    Track a page view (public endpoint).

    Records visitor page views for analytics. The raw client IP is hashed
    before persistence (GDPR pseudonymisation). PERF-01: geo-IP lookup is
    deferred to a `BackgroundTask` and back-fills the `country` column
    asynchronously so the response returns as soon as the row is inserted.
    """
    # Get client IP securely (only trusts X-Forwarded-For from known proxies)
    client_ip = get_client_ip(request)

    # Determine session_id: use visitor_id from frontend, or generate from IP hash
    if page_view.visitor_id:
        session_id = page_view.visitor_id
    else:
        # Fallback: generate anonymous session from a keyed hash of the IP.
        # See app/utils/ip_hash.py for the construction.
        session_id = f"anon_{hash_ip(client_ip)}"

    # Truncate to storage width: the schema accepts up to 2048 for
    # path/referrer (long UTM URLs are real traffic worth recording) but
    # the columns are String(500), and Postgres raises 22001 on overflow —
    # turning this unauthenticated beacon into a 500. The UA header is
    # attacker-sized (it bypasses body-size limits and the request
    # schema), so cap it before the unbounded Text column.
    #
    # _scrub also strips C0 control characters, which is the SAME class of
    # bug as the length overflow above and was missed by it: Postgres text
    # columns cannot store U+0000 at all, so a JSON-escaped \u0000 in
    # page_path/referrer/visitor_id raised DataError and 500'd this
    # unauthenticated endpoint (verified live, 2026-08-04). Stripping the
    # whole C0 range also keeps newlines and NULs out of log lines built
    # from these values — attacker-controlled log injection.
    page_path = _scrub(page_view.page_path, 500) or "/"
    referrer = _scrub(page_view.referrer, 500)
    session_id = _scrub(session_id, 255) or f"anon_{hash_ip(client_ip)}"
    user_agent = _scrub(request.headers.get("User-Agent"), 512)

    db_pageview = PageView(
        page_path=page_path,
        referrer=referrer,
        user_agent=user_agent,
        ip_address=hash_ip(client_ip),
        country=None,
        session_id=session_id,
    )
    db.add(db_pageview)
    await db.commit()
    await db.refresh(db_pageview)

    # Schedule the geo-IP back-fill AFTER the response goes out. Starlette
    # awaits background_tasks before closing the connection but only after
    # the response body has been sent — the client sees no extra latency.
    background_tasks.add_task(_backfill_country, str(db_pageview.id), client_ip)

    return PageViewResponse(
        id=str(db_pageview.id),
        visitor_id=str(db_pageview.session_id) if db_pageview.session_id else "anonymous",
        page_path=str(db_pageview.page_path),
        page_title=None,
        referrer=str(db_pageview.referrer) if db_pageview.referrer else None,
        timestamp=db_pageview.created_at or datetime.now(UTC),
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

    # D3-M-01 (honest signals): outbound clicks are recorded as synthetic
    # '/event/outbound/...' page views (trackEvent). Keep them OUT of the
    # real page-view metrics so total_views / top_pages / daily_views reflect
    # actual pages, then aggregate them separately below.
    #
    # '/admin%' is excluded for the same reason: router.afterEach used to fire
    # on admin navigations too, so the owner's own CMS sessions were counted as
    # visitor traffic. The frontend no longer sends them, but the rows already
    # in the table would keep skewing every window that reaches back far
    # enough -- filter at read time so history reads honestly too.
    is_real_page = PageView.page_path.not_like("/event/%") & PageView.page_path.not_like("/admin%")

    # Total page views (real pages only)
    total_result = await db.execute(
        select(func.count(PageView.id)).where(PageView.created_at >= cutoff, is_real_page)
    )
    total_views = total_result.scalar() or 0

    # Unique visitors (by session_id) — sessions that recorded at least one
    # real page view. Event-only rows never occur without a real view in the
    # same session, but an admin-only session does, so the same filter has to
    # apply here or the owner's own CMS sessions count as visitors.
    unique_result = await db.execute(
        select(func.count(func.distinct(PageView.session_id))).where(
            PageView.created_at >= cutoff, is_real_page
        )
    )
    unique_visitors = unique_result.scalar() or 0

    # Top pages (real pages only)
    top_pages_result = await db.execute(
        select(PageView.page_path, func.count(PageView.id).label("views"))
        .where(PageView.created_at >= cutoff, is_real_page)
        .group_by(PageView.page_path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    top_pages = [
        TopPage(path=row.page_path, title=None, views=row.views) for row in top_pages_result.all()
    ]

    # Daily views (real pages only)
    daily_views_result = await db.execute(
        select(
            func.date(PageView.created_at).label("date"),
            func.count(PageView.id).label("views"),
        )
        .where(PageView.created_at >= cutoff, is_real_page)
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
    )
    daily_views = [
        DailyView(date=str(row.date), views=row.views) for row in daily_views_result.all()
    ]

    # Outbound clicks: aggregate the '/event/outbound/<dest>/<label>' rows,
    # stripping the prefix so the dashboard shows e.g. 'linkedin/hero'.
    outbound_result = await db.execute(
        select(PageView.page_path, func.count(PageView.id).label("count"))
        .where(PageView.created_at >= cutoff, PageView.page_path.like("/event/outbound/%"))
        .group_by(PageView.page_path)
        .order_by(func.count(PageView.id).desc())
        .limit(10)
    )
    outbound_clicks = [
        OutboundClick(
            destination=row.page_path.removeprefix("/event/outbound/"),
            # _mapping["count"]: attribute access (row.count) shadows
            # tuple.count in the type stubs and mypy rejects it.
            count=row._mapping["count"],
        )
        for row in outbound_result.all()
    ]

    return AnalyticsStats(
        total_views=total_views,
        unique_visitors=unique_visitors,
        avg_session_duration=0,  # Would require session tracking
        top_pages=top_pages,
        daily_views=daily_views,
        period_days=days,
        outbound_clicks=outbound_clicks,
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
        # _mapping["count"]: see the outbound_clicks note above.
        TopCountry(country=row.country, count=row._mapping["count"])
        for row in countries_result.all()
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
