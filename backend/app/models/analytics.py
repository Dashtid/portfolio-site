"""
Analytics model for tracking page views
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text, func

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
