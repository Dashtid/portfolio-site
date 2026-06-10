"""
Refresh-token persistence for rotation + revocation tracking.

The JWT itself remains the bearer credential, but we now also persist its
`jti` server-side so /auth/refresh can:

- atomically rotate (mark current jti revoked, issue a new one), and
- detect replay of a stolen-but-revoked refresh token (per RFC 6819 §5.2.2.3)
  and revoke all of the user's outstanding tokens as a result.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from app.database import Base


class RefreshToken(Base):
    """Server-side record of an issued refresh-token JWT."""

    __tablename__ = "refresh_tokens"

    # The `jti` claim from the JWT. Url-safe random string. Primary key so
    # an attempted reuse of an already-rotated jti collides at insert and
    # surfaces in logs.
    jti = Column(String(64), primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    # Non-null timestamp means the token has been used in a rotation OR
    # explicitly revoked. Any subsequent /auth/refresh that decodes to this
    # jti is a replay attempt — see auth.refresh_token_endpoint.
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def is_expired(self, now: datetime | None = None) -> bool:
        moment = now or datetime.now(UTC)
        # SQLite returns naive datetimes; reattach UTC so the compare is sane.
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return exp <= moment
