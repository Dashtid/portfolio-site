"""
OAuth State model for distributed state storage

Stores OAuth states in the database instead of memory,
enabling multi-instance deployments (Fly.io, Kubernetes, etc.)
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class OAuthState(Base):
    """OAuth state for CSRF protection during OAuth flows"""

    __tablename__ = "oauth_states"

    # PRIMARY KEY already implies an index; the previous explicit index=True
    # was a no-op duplicate that some DBs (Postgres) materialise as a second
    # btree on the same column. Removed per DB-09.
    state = Column(String(64), primary_key=True)
    # Indexed per PERF-02: cleanup_oauth_states_periodically() filters by
    # `expires_at < now` every 5 minutes; without an index that's a full scan.
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    # server_default per DB-06: a row inserted out-of-band (seed scripts,
    # raw SQL) still gets a created_at without relying on the Python-side
    # default firing.
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    # Client IP binding for enhanced CSRF protection
    # The state can only be validated from the same IP that initiated the flow
    client_ip = Column(String(45), nullable=True)  # IPv6 max length is 45 chars

    def is_expired(self) -> bool:
        """Check if the state has expired"""
        now = datetime.now(UTC)
        # Handle SQLite returning naive datetimes (assume UTC)
        expires: datetime = self.expires_at  # type: ignore[assignment]
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return now > expires
