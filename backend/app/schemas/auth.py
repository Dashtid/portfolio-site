"""
Authentication schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema"""

    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class TokenData(BaseModel):
    """Token data schema"""

    user_id: str | None = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema with validation"""

    refresh_token: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="JWT refresh token",
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
