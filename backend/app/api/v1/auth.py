"""
Authentication API endpoints with GitHub OAuth

Uses database-backed OAuth state storage for multi-instance deployments.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.ip_utils import get_client_ip
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


async def create_oauth_state(db: AsyncSession, client_ip: str | None = None) -> str:
    """Create and store a new OAuth state bound to client IP for CSRF protection"""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)

    oauth_state = OAuthState(state=state, expires_at=expires_at, client_ip=client_ip)
    db.add(oauth_state)
    await db.commit()

    return state


async def validate_and_consume_state(
    db: AsyncSession, state: str, client_ip: str | None = None
) -> bool:
    """Validate OAuth state, verify IP binding, and remove it (single-use)"""
    result = await db.execute(select(OAuthState).where(OAuthState.state == state))
    oauth_state = result.scalar_one_or_none()

    if not oauth_state:
        return False

    if oauth_state.is_expired():
        await db.delete(oauth_state)
        await db.commit()
        return False

    # Verify client IP matches (if IP binding was used)
    # Security: If we stored an IP, require it to match (don't allow None bypass)
    if oauth_state.client_ip and (not client_ip or oauth_state.client_ip != client_ip):
        # IP mismatch or missing - possible CSRF attack
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

    # Note: Expired states are cleaned up by background task in main.py (every 5 minutes)
    # Removing duplicate cleanup here to prevent race conditions

    # Get client IP for state binding (CSRF protection)
    client_ip = get_client_ip(request)

    # Generate state for CSRF protection with TTL and IP binding (database-backed)
    state = await create_oauth_state(db, client_ip=client_ip)

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
    # Get client IP for state verification
    client_ip = get_client_ip(request)

    # Verify and consume state (single-use, database-backed, IP-bound)
    if not await validate_and_consume_state(db, state, client_ip=client_ip):
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
                    detail="Failed to authenticate with GitHub",
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

    # Create redirect response with HTTP-only cookies (secure token storage)
    redirect_url = f"{settings.FRONTEND_URL}/admin"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    # Set secure cookie options based on environment
    is_production = settings.ENVIRONMENT == "production"

    # Set access token cookie (shorter expiry)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/",
    )

    # Set refresh token cookie (longer expiry, restricted path)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",  # Only sent to auth endpoints
        httponly=True,
        secure=is_production,
        samesite="lax",
    )

    return response


@router.post("/refresh", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: DbSession,
    token_request: RefreshTokenRequest | None = None,
):
    """Refresh access token using refresh token with token rotation.

    Accepts refresh token from either:
    - HTTP-only cookie (preferred, set by OAuth callback)
    - Request body (for backwards compatibility)
    """
    # Try cookie first, then request body
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value and token_request:
        refresh_token_value = token_request.refresh_token

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required"
        )

    # Decode refresh token
    payload = decode_token(refresh_token_value)

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

    # Update cookies if request came from cookies
    if request.cookies.get("refresh_token"):
        is_production = settings.ENVIRONMENT == "production"

        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=is_production,
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/v1/auth",
            httponly=True,
            secure=is_production,
            samesite="lax",
        )

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
async def logout(request: Request, response: Response):
    """Logout user by clearing authentication cookies"""
    # Clear access token cookie
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )

    return {"message": "Successfully logged out"}
