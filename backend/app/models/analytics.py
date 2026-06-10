"""
Analytics model for tracking page views
"""

import uuid

from sqlalchemy import Column, DateTime, Index, String, Text, func

from app.database import Base


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_path = Column(String(500), nullable=False)
    referrer = Column(String(500))
    user_agent = Column(Text)
    ip_address = Column(String(64))  # Hashed IP (SHA-256 truncated to 16 hex chars)
    country = Column(String(2))  # ISO country code
    city = Column(String(100))
    session_id = Column(String(255), nullable=False, index=True)

    # Timestamps — indexed for analytics time-range queries
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # PERF-03: composite indexes for the analytics aggregation queries in
    # app/api/v1/analytics.py. Both endpoints filter on `created_at >= cutoff`
    # and then group by either page_path or country; without these indexes
    # SQLite/Postgres do a full scan of page_views before the GROUP BY. The
    # column order (created_at first) matches the WHERE-then-GROUP-BY pattern.
    __table_args__ = (
        Index("ix_page_views_created_path", "created_at", "page_path"),
        Index("ix_page_views_created_country", "created_at", "country"),
    )
