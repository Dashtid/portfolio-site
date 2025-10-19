"""
Authentication schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token data schema"""
    user_id: Optional[str] = None


class GitHubUser(BaseModel):
    """GitHub user data schema"""
    id: int
    login: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema"""
    id: str
    github_id: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True