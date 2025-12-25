"""
Authentication API endpoints with GitHub OAuth

Uses database-backed OAuth state storage for multi-instance deployments.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.database import get_db
from app.middleware import limiter
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.schemas.auth import RefreshTokenRequest, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

# OAuth state TTL
OAUTH_STATE_TTL_SECONDS = 300  # 5 minutes


async def cleanup_expired_states(db: AsyncSession) -> None:
    """Remove expired OAuth states from database"""
    await db.execute(delete(OAuthState).where(OAuthState.expires_at < datetime.now(UTC)))
    await db.commit()


async def create_oauth_state(db: AsyncSession) -> str:
    """Create and store a new OAuth state"""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)

    oauth_state = OAuthState(state=state, expires_at=expires_at)
    db.add(oauth_state)
    await db.commit()

    return state


async def validate_and_consume_state(db: AsyncSession, state: str) -> bool:
    """Validate OAuth state and remove it (single-use)"""
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        return False

    if oauth_state.is_expired():
        await db.delete(oauth_state)
        await db.commit()
        return False

    # Consume the state (single-use)
    await db.delete(oauth_state)
    await db.commit()
    return True


@router.get("/github")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_login(request: Request, db: DbSession):
    """Initiate GitHub OAuth flow"""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OAuth not configured"
        )

    # Cleanup expired states periodically
    await cleanup_expired_states(db)

    # Generate state for CSRF protection with TTL (database-backed)
    state = await create_oauth_state(db)

    # Build GitHub authorization URL
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=read:user user:email&"
        f"state={state}"
    )

    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_callback(request: Request, code: str, state: str, db: DbSession):
    """Handle GitHub OAuth callback"""
    # Verify and consume state (single-use, database-backed)
    if not await validate_and_consume_state(db, state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state parameter"
        )

    # Exchange code for access token with proper timeout and error handling
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get access token from GitHub
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get access token from GitHub",
                )

            token_data = token_response.json()

            if "error" in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=token_data.get("error_description", "OAuth error"),
                )

            github_access_token = token_data.get("access_token")

            # Get user info from GitHub
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {github_access_token}",
                    "Accept": "application/json",
                },
            )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from GitHub",
                )

            github_user = user_response.json()
    except httpx.TimeoutException as err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub service is not responding. Please try again later.",
        ) from err
    except httpx.RequestError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with authentication service. Please try again.",
        ) from err

    # Check if user is the admin
    github_id = str(github_user.get("id"))

    if settings.ADMIN_GITHUB_ID and github_id != settings.ADMIN_GITHUB_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the admin can log in"
        )

    # Check if user exists in database
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    # Create or update user
    if not user:
        user = User(
            github_id=github_id,
            username=github_user.get("login"),
            email=github_user.get("email"),
            name=github_user.get("name"),
            avatar_url=github_user.get("avatar_url"),
            is_admin=True,  # Since we only allow admin login
        )
        db.add(user)
    else:
        # Update user info
        user.username = github_user.get("login")
        user.email = github_user.get("email")
        user.name = github_user.get("name")
        user.avatar_url = github_user.get("avatar_url")

    await db.commit()
    await db.refresh(user)

    # Create JWT tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # Redirect to frontend with tokens
    redirect_url = f"{settings.FRONTEND_URL}/admin?token={access_token}&refresh={refresh_token}"
    return RedirectResponse(url=redirect_url)


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh_token_endpoint(
    request: Request, token_request: RefreshTokenRequest, db: DbSession
):
    """Refresh access token using refresh token with token rotation"""
    # Decode refresh token (validated by Pydantic schema)
    payload = decode_token(token_request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Create new tokens (refresh token rotation for security - 2025 best practice)
    # This prevents refresh token reuse attacks - each token is single-use
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
    }


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_API)
async def get_current_user_info(request: Request, current_user: CurrentUser):
    """Get current user information"""
    return current_user


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_API)
async def logout(request: Request):
    """Logout user (client-side token removal)"""
    # In a production app, you might want to blacklist the token
    # For now, we just return a success message
    return {"message": "Successfully logged out"}
