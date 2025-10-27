"""
Analytics model for tracking page views
"""

import uuid

from sqlalchemy import Column, DateTime, String, Text, func

from app.database import Base


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    page_path = Column(String(500))
    referrer = Column(String(500))
    user_agent = Column(Text)
    ip_address = Column(String(45))  # Support IPv6
    country = Column(String(2))  # ISO country code
    city = Column(String(100))
    session_id = Column(String(255))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "page_path": self.page_path,
            "referrer": self.referrer,
            "country": self.country,
            "city": self.city,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
