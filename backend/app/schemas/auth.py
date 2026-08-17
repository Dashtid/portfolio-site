"""
Authentication schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """Token data schema"""

    user_id: str | None = None


class RefreshSuccess(BaseModel):
    """Refresh-endpoint response. Tokens are delivered via HTTP-only cookies;
    the body is intentionally token-free so an XSS payload calling /auth/refresh
    cannot lift the new credentials from the JSON response."""

    refreshed: bool = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema with validation.

    ``refresh_token`` is OPTIONAL because the primary delivery channel is the
    HTTP-only ``refresh_token`` cookie — the browser client cannot read that
    cookie, so it POSTs an empty ``{}`` body and lets the endpoint pick the
    token off the request. While this field was required, that empty body
    failed validation and the endpoint answered 422 instead of reaching its
    own 401 "Refresh token required" branch, so every unauthenticated visit
    to an /admin URL logged a console error.
    """

    refresh_token: str | None = Field(
        default=None,
        min_length=10,
        max_length=2000,
        description="JWT refresh token (omit when supplying it via the refresh_token cookie)",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )


class GitHubUser(BaseModel):
    """GitHub user data schema"""

    id: int
    login: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class UserBase(BaseModel):
    """Base user schema"""

    username: str
    email: str | None = None
    name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """User response schema"""

    id: str
    github_id: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}
