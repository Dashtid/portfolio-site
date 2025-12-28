"""
OAuth State model for distributed state storage

Stores OAuth states in the database instead of memory,
enabling multi-instance deployments (Fly.io, Kubernetes, etc.)
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String

from app.database import Base


class OAuthState(Base):
    """OAuth state for CSRF protection during OAuth flows"""

    __tablename__ = "oauth_states"

    state = Column(String(64), primary_key=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Client IP binding for enhanced CSRF protection
    # The state can only be validated from the same IP that initiated the flow
    client_ip = Column(String(45), nullable=True)  # IPv6 max length is 45 chars

    def is_expired(self) -> bool:
        """Check if the state has expired"""
        now = datetime.now(UTC)
        # Handle SQLite returning naive datetimes (assume UTC)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return now > expires
